#!/usr/bin/env python3
"""
Script d'évaluation du pipeline de génération de tests IA - PFE04
Évalue la qualité des LLM (Gemini, DeepSeek, Mistral) pour générer des tests RestAssured
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
import logging
import random
import csv
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
from pathlib import Path

# ====== CONFIGURATION INTÉGRÉE ======
# URLs des services
BACKEND_URL = "http://localhost:5000"
MISTRAL_URL = "http://127.0.0.1:8000"

# Critères de qualité pour l'évaluation des tests générés
QUALITY_CRITERIA = {
    "minimum_imports": ["import", "RestAssured", "SpringBootTest"],
    "required_annotations": ["@Test", "@SpringBootTest"],
    "assertion_keywords": ["assert", "expect", "verify", "should"],
    "restassured_patterns": ["given()", "when()", "then()", ".body()", ".statusCode()"],
    "best_practices": ["@DisplayName", "@BeforeEach"],
    "status_codes": ["200", "201", "400", "404", "500"]
}

# Seuils de performance
PERFORMANCE_THRESHOLDS = {
    "max_response_time": 10.0,
    "min_success_rate": 80.0,
    "min_quality_score": 60.0
}

# Configuration pour tests massifs - GEMINI UNIQUEMENT
MASSIVE_TEST_CONFIG = {
    "tests_per_llm": 150,  # Nombre de tests pour Gemini (centaines de tests)
    "batch_size": 8,       # Tests par batch pour éviter surcharge
    "delay_between_batches": 1,  # Pause entre batches (secondes)
    "max_concurrent": 3,   # Requêtes simultanées max (plus conservateur)
    "timeout_per_test": 45, # Timeout par test individual (plus long)
    "gemini_only": True    # Mode Gemini uniquement
}

# Générateur d'échantillons d'API variés pour tests massifs
def generate_api_samples():
    """Génère une grande variété d'échantillons d'API pour tests exhaustifs"""
    
    # Templates de base
    base_samples = [
        # APIs simples - CRUD basique
        {
            "name": "User Management API",
            "complexity": "simple",
            "code": """
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        return ResponseEntity.ok(user);
    }
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User savedUser = userService.save(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedUser);
    }
}"""
        },
        
        # APIs medium - avec validation
        {
            "name": "Product Catalog API",
            "complexity": "medium", 
            "code": """
@RestController
@RequestMapping("/api/products")
public class ProductController {
    @GetMapping
    public ResponseEntity<Page<Product>> getAllProducts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        Page<Product> products = productService.findAll(PageRequest.of(page, size));
        return ResponseEntity.ok(products);
    }
    
    @PostMapping
    public ResponseEntity<Product> createProduct(@Valid @RequestBody ProductDto productDto) {
        Product product = productService.create(productDto);
        return ResponseEntity.status(HttpStatus.CREATED).body(product);
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<Product> updateProduct(@PathVariable Long id, @Valid @RequestBody ProductDto productDto) {
        Product updated = productService.update(id, productDto);
        return ResponseEntity.ok(updated);
    }
}"""
        },
        
        # APIs complexes - avec sécurité et gestion d'erreurs
        {
            "name": "Order Processing API",
            "complexity": "complex",
            "code": """
@RestController
@RequestMapping("/api/orders")
@PreAuthorize("hasRole('USER')")
public class OrderController {
    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(@Valid @RequestBody OrderRequest request, Authentication auth) {
        try {
            OrderResponse response = orderService.processOrder(request, auth.getName());
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (InsufficientStockException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(new OrderResponse("OUT_OF_STOCK", e.getMessage()));
        } catch (PaymentException e) {
            return ResponseEntity.status(HttpStatus.PAYMENT_REQUIRED)
                .body(new OrderResponse("PAYMENT_FAILED", e.getMessage()));
        }
    }
    
    @GetMapping("/{orderId}")
    public ResponseEntity<OrderDetails> getOrder(@PathVariable String orderId, Authentication auth) {
        OrderDetails order = orderService.findByIdAndUser(orderId, auth.getName());
        return ResponseEntity.ok(order);
    }
    
    @PatchMapping("/{orderId}/cancel")
    public ResponseEntity<Void> cancelOrder(@PathVariable String orderId, Authentication auth) {
        orderService.cancelOrder(orderId, auth.getName());
        return ResponseEntity.noContent().build();
    }
}"""
        },
        
        # APIs avec upload de fichiers
        {
            "name": "File Upload API",
            "complexity": "medium",
            "code": """
@RestController
@RequestMapping("/api/files")
public class FileUploadController {
    @PostMapping("/upload")
    public ResponseEntity<FileResponse> uploadFile(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(new FileResponse("FILE_EMPTY", "File is empty"));
        }
        try {
            String fileId = fileService.store(file);
            return ResponseEntity.ok(new FileResponse("SUCCESS", fileId));
        } catch (StorageException e) {
            return ResponseEntity.status(HttpStatus.INSUFFICIENT_STORAGE)
                .body(new FileResponse("STORAGE_ERROR", e.getMessage()));
        }
    }
    
    @GetMapping("/download/{fileId}")
    public ResponseEntity<Resource> downloadFile(@PathVariable String fileId) {
        Resource file = fileService.loadAsResource(fileId);
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + file.getFilename() + "\"")
            .body(file);
    }
}"""
        },
        
        # APIs de recherche avec filtres
        {
            "name": "Search API",
            "complexity": "complex",
            "code": """
@RestController
@RequestMapping("/api/search")
public class SearchController {
    @GetMapping("/products")
    public ResponseEntity<SearchResults<Product>> searchProducts(
            @RequestParam String query,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) Double minPrice,
            @RequestParam(required = false) Double maxPrice,
            @RequestParam(defaultValue = "relevance") String sortBy,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        
        SearchCriteria criteria = SearchCriteria.builder()
            .query(query)
            .category(category)
            .priceRange(minPrice, maxPrice)
            .sortBy(sortBy)
            .pagination(page, size)
            .build();
            
        SearchResults<Product> results = searchService.searchProducts(criteria);
        return ResponseEntity.ok(results);
    }
}"""
        }
    ]
    
    # Générer des variations pour atteindre des centaines d'échantillons
    api_samples = []
    
    # Multiplier les échantillons de base avec variations
    entities = ["User", "Product", "Order", "Category", "Review", "Payment", "Shipping", "Inventory", "Customer", "Supplier"]
    operations = ["find", "create", "update", "delete", "search", "validate", "process", "calculate"]
    
    for base_sample in base_samples:
        # Ajouter l'échantillon original
        api_samples.append(base_sample)
        
        # Créer des variations en changeant les noms d'entités
        for i, entity in enumerate(entities[:8]):  # 8 variations par échantillon de base
            variation = base_sample.copy()
            variation["name"] = f"{entity} {base_sample['name']}"
            variation["code"] = base_sample["code"].replace("User", entity).replace("Product", entity).replace("Order", entity)
            api_samples.append(variation)
    
    return api_samples

# Charger tous les échantillons d'API
API_SAMPLES = generate_api_samples()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Structure pour stocker les résultats d'un test"""
    test_name: str
    success: bool
    execution_time: float
    response_time: float
    response_status: int
    response_size: int
    error_message: str = ""
    coverage_metrics: Dict = None
    quality_score: float = 0.0
    
    def to_dict(self):
        return asdict(self)

@dataclass
class SystemMetrics:
    """Métriques globales du système"""
    total_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    avg_response_time: float = 0.0
    avg_execution_time: float = 0.0
    success_rate: float = 0.0
    avg_quality_score: float = 0.0
    coverage_analysis: Dict = None
    total_execution_time: float = 0.0
    
class AutoTestPrototypeTester:
    """Classe principale pour tester le prototype d'IA de génération de tests"""
    
    def __init__(self):
        # Configuration des URLs
        self.frontend_url = "http://localhost:3000"
        self.backend_url = "http://localhost:5000"
        self.mistral_url = "http://127.0.0.1:8000"
        
        # Stockage des résultats
        self.test_results: List[TestResult] = []
        self.system_metrics = SystemMetrics()
        
        # Métriques spécifiques pour évaluer le pipeline de génération
        self.pipeline_metrics = {
            "llm_quality_scores": {},  # Score par modèle LLM
            "generation_consistency": {},  # Consistance des générations
            "code_coverage_improvement": [],  # Amélioration de la couverture
            "test_execution_success_rate": {},  # Taux de succès d'exécution
            "snippet_complexity_handling": {}  # Gestion de complexité des snippets
        }
        
        # Exemples de code API Spring Boot pour tester le pipeline
        self.api_samples = self._generate_api_samples()
        
        # Session HTTP réutilisable
        self.session = None
        
    def _generate_api_samples(self) -> List[Dict[str, str]]:
        """Génère des échantillons de code API Spring Boot diversifiés"""
        return [
            {
                "name": "Simple REST Controller",
                "code": """
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        User user = userService.findById(id);
        if (user != null) {
            return ResponseEntity.ok(user);
        }
        return ResponseEntity.notFound().build();
    }
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User savedUser = userService.save(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedUser);
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<User> updateUser(@PathVariable Long id, @RequestBody User user) {
        User updatedUser = userService.update(id, user);
        return ResponseEntity.ok(updatedUser);
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        userService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
"""
            },
            {
                "name": "Complex Business Logic Controller",
                "code": """
@RestController
@RequestMapping("/api/orders")
@Validated
public class OrderController {
    
    @Autowired
    private OrderService orderService;
    
    @Autowired
    private PaymentService paymentService;
    
    @GetMapping
    public ResponseEntity<Page<Order>> getAllOrders(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String status) {
        
        Pageable pageable = PageRequest.of(page, size);
        Page<Order> orders = orderService.findAll(status, pageable);
        return ResponseEntity.ok(orders);
    }
    
    @PostMapping
    @Transactional
    public ResponseEntity<Order> createOrder(@Valid @RequestBody CreateOrderRequest request) {
        try {
            Order order = orderService.createOrder(request);
            PaymentResult payment = paymentService.processPayment(order.getTotal());
            
            if (payment.isSuccessful()) {
                order.setStatus(OrderStatus.CONFIRMED);
                orderService.save(order);
                return ResponseEntity.status(HttpStatus.CREATED).body(order);
            } else {
                order.setStatus(OrderStatus.FAILED);
                orderService.save(order);
                return ResponseEntity.badRequest().build();
            }
        } catch (InsufficientStockException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(new ErrorResponse("Insufficient stock", e.getMessage()));
        }
    }
    
    @GetMapping("/{orderId}/tracking")
    public ResponseEntity<TrackingInfo> getOrderTracking(@PathVariable String orderId) {
        TrackingInfo tracking = orderService.getTracking(orderId);
        return ResponseEntity.ok(tracking);
    }
}
"""
            },
            {
                "name": "Security-focused API",
                "code": """
@RestController
@RequestMapping("/api/auth")
@PreAuthorize("hasRole('ADMIN')")
public class AuthController {
    
    @Autowired
    private AuthenticationService authService;
    
    @PostMapping("/login")
    @AllowAnonymous
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        try {
            AuthResponse response = authService.authenticate(request);
            return ResponseEntity.ok(response);
        } catch (BadCredentialsException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
    }
    
    @PostMapping("/refresh")
    public ResponseEntity<AuthResponse> refreshToken(@RequestHeader("Authorization") String token) {
        String jwt = token.substring(7); // Remove "Bearer "
        AuthResponse response = authService.refreshToken(jwt);
        return ResponseEntity.ok(response);
    }
    
    @PostMapping("/logout")
    public ResponseEntity<Void> logout(HttpServletRequest request) {
        String token = extractToken(request);
        authService.invalidateToken(token);
        return ResponseEntity.ok().build();
    }
    
    @GetMapping("/profile")
    @PreAuthorize("hasRole('USER') or hasRole('ADMIN')")
    public ResponseEntity<UserProfile> getProfile(Authentication auth) {
        UserProfile profile = authService.getUserProfile(auth.getName());
        return ResponseEntity.ok(profile);
    }
}
"""
            },
            {
                "name": "Microservice with External APIs",
                "code": """
@RestController
@RequestMapping("/api/weather")
public class WeatherController {
    
    @Autowired
    private WeatherService weatherService;
    
    @Autowired
    private CacheService cacheService;
    
    @GetMapping("/current/{city}")
    @Cacheable("weather")
    public ResponseEntity<WeatherInfo> getCurrentWeather(@PathVariable String city) {
        try {
            WeatherInfo weather = weatherService.getCurrentWeather(city);
            return ResponseEntity.ok(weather);
        } catch (CityNotFoundException e) {
            return ResponseEntity.notFound().build();
        } catch (ExternalServiceException e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).build();
        }
    }
    
    @GetMapping("/forecast/{city}")
    public ResponseEntity<List<WeatherForecast>> getForecast(
            @PathVariable String city,
            @RequestParam(defaultValue = "5") int days) {
        
        if (days > 14) {
            return ResponseEntity.badRequest().build();
        }
        
        List<WeatherForecast> forecast = weatherService.getForecast(city, days);
        return ResponseEntity.ok(forecast);
    }
    
    @PostMapping("/alerts")
    public ResponseEntity<AlertResponse> createWeatherAlert(@RequestBody WeatherAlert alert) {
        AlertResponse response = weatherService.createAlert(alert);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
"""
            },
            {
                "name": "File Upload and Processing API",
                "code": """
@RestController
@RequestMapping("/api/files")
public class FileController {
    
    @Autowired
    private FileStorageService storageService;
    
    @PostMapping("/upload")
    public ResponseEntity<FileUploadResponse> uploadFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam(required = false) String description) {
        
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        
        try {
            String filename = storageService.store(file);
            FileUploadResponse response = new FileUploadResponse(filename, file.getSize(), description);
            return ResponseEntity.ok(response);
        } catch (StorageException e) {
            return ResponseEntity.status(HttpStatus.INSUFFICIENT_STORAGE).build();
        }
    }
    
    @GetMapping("/download/{filename:.+}")
    public ResponseEntity<Resource> downloadFile(@PathVariable String filename) {
        Resource file = storageService.loadAsResource(filename);
        
        if (file.exists() || file.isReadable()) {
            return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + file.getFilename() + "\"")
                .body(file);
        } else {
            return ResponseEntity.notFound().build();
        }
    }
    
    @DeleteMapping("/{filename:.+}")
    public ResponseEntity<Void> deleteFile(@PathVariable String filename) {
        try {
            storageService.delete(filename);
            return ResponseEntity.noContent().build();
        } catch (StorageFileNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }
}
"""
            }
        ]
    
    async def setup_session(self):
        """Configure la session HTTP asynchrone"""
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
    
    async def cleanup_session(self):
        """Nettoie la session HTTP"""
        if self.session:
            await self.session.close()
    
    async def test_backend_health(self) -> TestResult:
        """Test de santé du backend"""
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.backend_url}/health") as response:
                execution_time = time.time() - start_time
                
                return TestResult(
                    test_name="Backend Health Check",
                    success=response.status == 200,
                    execution_time=execution_time,
                    response_time=execution_time,
                    response_status=response.status,
                    response_size=len(await response.text()) if response.status == 200 else 0
                )
        except Exception as e:
            return TestResult(
                test_name="Backend Health Check",
                success=False,
                execution_time=time.time() - start_time,
                response_time=0.0,
                response_status=0,
                response_size=0,
                error_message=str(e)
            )
    
    async def test_gemini_test_generation(self, api_sample: Dict[str, str]) -> TestResult:
        """Test de génération de tests avec Gemini - Focus sur l'évaluation du pipeline"""
        start_time = time.time()
        
        try:
            payload = {"api_code": api_sample["code"]}
            
            async with self.session.post(
                f"{self.backend_url}/rest-assured-test/gemini",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_text = await response.text()
                execution_time = time.time() - start_time
                
                success = response.status == 200
                if success:
                    response_json = json.loads(response_text)
                    generated_test = response_json.get("generated_test", "")
                    
                    # Évaluation spécifique du pipeline de génération
                    quality_score = self._analyze_test_quality(generated_test)
                    
                    # Stocker les métriques spécifiques au LLM
                    if "Gemini" not in self.pipeline_metrics["llm_quality_scores"]:
                        self.pipeline_metrics["llm_quality_scores"]["Gemini"] = []
                    self.pipeline_metrics["llm_quality_scores"]["Gemini"].append(quality_score)
                    
                    # Évaluer la capacité à générer des tests exécutables
                    is_executable = self._evaluate_test_executability(generated_test)
                    
                    # Mesurer la complexité du snippet traité
                    snippet_complexity = self._measure_snippet_complexity(api_sample["code"])
                    
                    return TestResult(
                        test_name=f"Pipeline-Gemini-{api_sample['name']}",
                        success=True,
                        execution_time=execution_time,
                        response_time=execution_time,
                        response_status=response.status,
                        response_size=len(response_text),
                        quality_score=quality_score,
                        # Ajout de métriques spécifiques au pipeline
                        error_message=f"Executable:{is_executable}|Complexity:{snippet_complexity}|Length:{len(generated_test)}"
                    )
                else:
                    return TestResult(
                        test_name=f"Pipeline-Gemini-{api_sample['name']}",
                        success=False,
                        execution_time=execution_time,
                        response_time=execution_time,
                        response_status=response.status,
                        response_size=len(response_text),
                        error_message=response_text
                    )
                    
        except Exception as e:
            return TestResult(
                test_name=f"Pipeline-Gemini-{api_sample['name']}",
                success=False,
                execution_time=time.time() - start_time,
                response_time=0.0,
                response_status=0,
                response_size=0,
                error_message=str(e)
            )
    
    def _evaluate_test_executability(self, test_code: str) -> bool:
        """Évalue si le test généré est potentiellement exécutable"""
        executable_indicators = [
            "class" in test_code and "Test" in test_code,
            "@Test" in test_code,
            "import" in test_code,
            any(assertion in test_code for assertion in ["assert", "expect", "verify"]),
            not any(error in test_code.lower() for error in ["error", "exception", "failed to generate"])
        ]
        return sum(executable_indicators) >= 4
    
    def _measure_snippet_complexity(self, api_code: str) -> str:
        """Mesure la complexité du snippet d'API"""
        endpoints_count = api_code.count("@GetMapping") + api_code.count("@PostMapping") + \
                         api_code.count("@PutMapping") + api_code.count("@DeleteMapping")
        lines_count = len(api_code.split('\n'))
        
        if endpoints_count <= 1 and lines_count <= 20:
            return "simple"
        elif endpoints_count <= 3 and lines_count <= 50:
            return "medium"
        else:
            return "complex"
    
    async def test_deepseek_test_generation(self, api_sample: Dict[str, str]) -> TestResult:
        """Test de génération de tests avec DeepSeek - Évaluation du pipeline"""
        start_time = time.time()
        
        try:
            payload = {"api_code": api_sample["code"]}
            
            async with self.session.post(
                f"{self.backend_url}/rest-assured-test",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_text = await response.text()
                execution_time = time.time() - start_time
                
                success = response.status == 200
                if success:
                    response_json = json.loads(response_text)
                    generated_test = response_json.get("generated_test", "")
                    
                    # Évaluation du pipeline avec DeepSeek
                    quality_score = self._analyze_test_quality(generated_test)
                    
                    # Stocker les métriques LLM
                    if "DeepSeek" not in self.pipeline_metrics["llm_quality_scores"]:
                        self.pipeline_metrics["llm_quality_scores"]["DeepSeek"] = []
                    self.pipeline_metrics["llm_quality_scores"]["DeepSeek"].append(quality_score)
                    
                    is_executable = self._evaluate_test_executability(generated_test)
                    snippet_complexity = self._measure_snippet_complexity(api_sample["code"])
                    
                    return TestResult(
                        test_name=f"Pipeline-DeepSeek-{api_sample['name']}",
                        success=True,
                        execution_time=execution_time,
                        response_time=execution_time,
                        response_status=response.status,
                        response_size=len(response_text),
                        quality_score=quality_score,
                        error_message=f"Executable:{is_executable}|Complexity:{snippet_complexity}|Length:{len(generated_test)}"
                    )
                else:
                    return TestResult(
                        test_name=f"Pipeline-DeepSeek-{api_sample['name']}",
                        success=False,
                        execution_time=execution_time,
                        response_time=execution_time,
                        response_status=response.status,
                        response_size=len(response_text),
                        error_message=response_text
                    )
                    
        except Exception as e:
            return TestResult(
                test_name=f"Pipeline-DeepSeek-{api_sample['name']}",
                success=False,
                execution_time=time.time() - start_time,
                response_time=0.0,
                response_status=0,
                response_size=0,
                error_message=str(e)
            )
    
    async def test_mistral_generation(self, api_sample: Dict[str, str]) -> TestResult:
        """Test de génération avec Mistral - Focus évaluation pipeline"""
        start_time = time.time()
        
        try:
            payload = {
                "prompt": api_sample["code"],
                "test_type": "RestAssured"
            }
            
            async with self.session.post(
                f"{self.mistral_url}/generate-test",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_text = await response.text()
                execution_time = time.time() - start_time
                
                success = response.status == 200
                if success:
                    response_json = json.loads(response_text)
                    generated_test = response_json.get("generated_test", "")
                    
                    # Évaluation du pipeline avec Mistral
                    quality_score = self._analyze_test_quality(generated_test)
                    
                    # Stocker les métriques LLM
                    if "Mistral" not in self.pipeline_metrics["llm_quality_scores"]:
                        self.pipeline_metrics["llm_quality_scores"]["Mistral"] = []
                    self.pipeline_metrics["llm_quality_scores"]["Mistral"].append(quality_score)
                    
                    is_executable = self._evaluate_test_executability(generated_test)
                    snippet_complexity = self._measure_snippet_complexity(api_sample["code"])
                    
                    return TestResult(
                        test_name=f"Pipeline-Mistral-{api_sample['name']}",
                        success=True,
                        execution_time=execution_time,
                        response_time=execution_time,
                        response_status=response.status,
                        response_size=len(response_text),
                        quality_score=quality_score,
                        error_message=f"Executable:{is_executable}|Complexity:{snippet_complexity}|Length:{len(generated_test)}"
                    )
                else:
                    return TestResult(
                        test_name=f"Pipeline-Mistral-{api_sample['name']}",
                        success=False,
                        execution_time=execution_time,
                        response_time=execution_time,
                        response_status=response.status,
                        response_size=len(response_text),
                        error_message=response_text
                    )
                    
        except Exception as e:
            return TestResult(
                test_name=f"Pipeline-Mistral-{api_sample['name']}",
                success=False,
                execution_time=time.time() - start_time,
                response_time=0.0,
                response_status=0,
                response_size=0,
                error_message=str(e)
            )
    
    async def test_execution_with_metrics(self, api_sample: Dict[str, str]) -> TestResult:
        """Test d'exécution de tests avec métriques JaCoCo"""
        start_time = time.time()
        
        try:
            # Première étape: générer un test
            test_gen_payload = {"api_code": api_sample["code"]}
            
            async with self.session.post(
                f"{self.backend_url}/rest-assured-test/gemini",
                json=test_gen_payload,
                headers={"Content-Type": "application/json"}
            ) as gen_response:
                
                if gen_response.status != 200:
                    return TestResult(
                        test_name=f"Test Execution with Metrics - {api_sample['name']}",
                        success=False,
                        execution_time=time.time() - start_time,
                        response_time=0.0,
                        response_status=gen_response.status,
                        response_size=0,
                        error_message="Failed to generate test for execution"
                    )
                
                gen_data = await gen_response.json()
                generated_test = gen_data.get("generated_test", "")
                
                # Deuxième étape: exécuter le test
                exec_payload = {
                    "test_code": generated_test,
                    "api_code": api_sample["code"]
                }
                
                async with self.session.post(
                    f"{self.backend_url}/execute-tests",
                    json=exec_payload,
                    headers={"Content-Type": "application/json"}
                ) as exec_response:
                    
                    exec_data = await exec_response.json()
                    execution_id = exec_data.get("execution_id")
                    
                    # Attendre la completion de l'exécution
                    await asyncio.sleep(2)  # Attendre un peu
                    
                    # Récupérer les métriques
                    async with self.session.get(
                        f"{self.backend_url}/execution-metrics/{execution_id}"
                    ) as metrics_response:
                        
                        execution_time = time.time() - start_time
                        
                        if metrics_response.status == 200:
                            metrics_data = await metrics_response.json()
                            
                            return TestResult(
                                test_name=f"Test Execution with Metrics - {api_sample['name']}",
                                success=True,
                                execution_time=execution_time,
                                response_time=execution_time,
                                response_status=200,
                                response_size=len(await metrics_response.text()),
                                coverage_metrics=metrics_data
                            )
                        else:
                            return TestResult(
                                test_name=f"Test Execution with Metrics - {api_sample['name']}",
                                success=False,
                                execution_time=execution_time,
                                response_time=execution_time,
                                response_status=metrics_response.status,
                                response_size=0,
                                error_message="Failed to retrieve metrics"
                            )
                            
        except Exception as e:
            return TestResult(
                test_name=f"Test Execution with Metrics - {api_sample['name']}",
                success=False,
                execution_time=time.time() - start_time,
                response_time=0.0,
                response_status=0,
                response_size=0,
                error_message=str(e)
            )
    
    def _analyze_test_quality(self, test_code: str) -> float:
        """Analyse la qualité d'un test généré par le pipeline"""
        if not test_code or len(test_code.strip()) == 0:
            return 0.0
        
        # Critères spécifiques pour évaluer votre pipeline de génération
        pipeline_quality_checks = {
            # Critères essentiels de génération (40 points)
            "has_imports": "import" in test_code,
            "has_test_annotation": "@Test" in test_code,
            "has_assertions": any(keyword in test_code.lower() for keyword in ["assert", "expect", "verify"]),
            "has_restassured": "RestAssured" in test_code or "given()" in test_code,
            
            # Qualité de l'architecture Spring Boot (30 points)
            "has_springboot_test": "@SpringBootTest" in test_code,
            "proper_class_structure": "class" in test_code and "{" in test_code and "}" in test_code,
            "has_test_port_config": "webEnvironment" in test_code or "RANDOM_PORT" in test_code,
            
            # Sophistication des tests générés (20 points)
            "has_multiple_scenarios": test_code.count("@Test") > 1,
            "has_status_assertions": any(status in test_code for status in ["200", "201", "400", "404", "500"]),
            "has_json_validation": "jsonPath" in test_code or "body()" in test_code,
            
            # Bonnes pratiques avancées (10 points)
            "has_display_name": "@DisplayName" in test_code,
            "has_setup_methods": "@BeforeEach" in test_code or "@Before" in test_code,
            "has_error_handling": any(keyword in test_code for keyword in ["try", "catch", "Exception"]),
            "has_parameterized": "@ParameterizedTest" in test_code
        }
        
        # Pondération selon l'importance pour votre pipeline
        weights = {
            "has_imports": 8, "has_test_annotation": 10, "has_assertions": 12, "has_restassured": 10,
            "has_springboot_test": 8, "proper_class_structure": 8, "has_test_port_config": 7,
            "has_multiple_scenarios": 5, "has_status_assertions": 7, "has_json_validation": 8,
            "has_display_name": 3, "has_setup_methods": 4, "has_error_handling": 5, "has_parameterized": 5
        }
        
        # Calculer le score pondéré
        total_possible = sum(weights.values())
        achieved_score = sum(weights[criterion] for criterion, met in pipeline_quality_checks.items() if met)
        
        quality_score = (achieved_score / total_possible) * 100
        
        return round(quality_score, 2)
    
    async def test_concurrent_requests(self, num_concurrent: int = 10) -> List[TestResult]:
        """Test de performance avec requêtes concurrentes"""
        logger.info(f"Testing {num_concurrent} concurrent requests...")
        
        # Sélectionner un échantillon d'API pour les tests concurrents
        api_sample = random.choice(self.api_samples)
        
        # Créer les tâches concurrentes
        tasks = []
        for i in range(num_concurrent):
            tasks.append(self.test_gemini_test_generation(api_sample))
        
        # Exécuter toutes les tâches en parallèle
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les résultats
        test_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_results.append(TestResult(
                    test_name=f"Concurrent Request {i+1}",
                    success=False,
                    execution_time=0.0,
                    response_time=0.0,
                    response_status=0,
                    response_size=0,
                    error_message=str(result)
                ))
            else:
                result.test_name = f"Concurrent Request {i+1}"
                test_results.append(result)
        
        return test_results
    
    async def test_stress_load(self, duration_seconds: int = 60) -> List[TestResult]:
        """Test de charge pendant une durée spécifiée"""
        logger.info(f"Running stress test for {duration_seconds} seconds...")
        
        results = []
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < duration_seconds:
            api_sample = random.choice(self.api_samples)
            
            # Alterner entre les différents endpoints
            if request_count % 3 == 0:
                result = await self.test_gemini_test_generation(api_sample)
            elif request_count % 3 == 1:
                result = await self.test_deepseek_test_generation(api_sample)
            else:
                result = await self.test_mistral_generation(api_sample)
            
            result.test_name = f"Stress Test Request {request_count + 1}"
            results.append(result)
            request_count += 1
            
            # Petite pause pour éviter de surcharger
            await asyncio.sleep(0.1)
        
        logger.info(f"Completed {request_count} requests in stress test")
        return results
    
    async def test_edge_cases(self) -> List[TestResult]:
        """Test des cas limites et cas d'erreur"""
        edge_case_tests = []
        
        # Test avec code vide
        empty_code_test = await self.test_gemini_test_generation({
            "name": "Empty Code",
            "code": ""
        })
        empty_code_test.test_name = "Edge Case - Empty Code"
        edge_case_tests.append(empty_code_test)
        
        # Test avec code invalide
        invalid_code_test = await self.test_gemini_test_generation({
            "name": "Invalid Java Code",
            "code": "this is not valid java code $$$ !!!"
        })
        invalid_code_test.test_name = "Edge Case - Invalid Code"
        edge_case_tests.append(invalid_code_test)
        
        # Test avec code très long
        long_code = self.api_samples[0]["code"] * 50  # Répéter 50 fois
        long_code_test = await self.test_gemini_test_generation({
            "name": "Very Long Code",
            "code": long_code
        })
        long_code_test.test_name = "Edge Case - Very Long Code"
        edge_case_tests.append(long_code_test)
        
        # Test avec caractères spéciaux
        special_chars_test = await self.test_gemini_test_generation({
            "name": "Special Characters",
            "code": "@RestController\npublic class TestController {\n    @GetMapping(\"/test\")\n    public String test() {\n        return \"Héllo Wörld! 中文 🚀\";\n    }\n}"
        })
        special_chars_test.test_name = "Edge Case - Special Characters"
        edge_case_tests.append(special_chars_test)
        
        return edge_case_tests
    
    async def test_pipeline_consistency(self) -> List[TestResult]:
        """Test spécifique pour évaluer la consistance du pipeline de génération"""
        consistency_results = []
        
        # Test de reproductibilité - même code, multiples générations
        baseline_api = {
            "name": "Consistency Baseline",
            "code": """
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        return user != null ? ResponseEntity.ok(user) : ResponseEntity.notFound().build();
    }
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User created = userService.save(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }
}
"""
        }
        
        # Générer 5 fois le même test avec chaque LLM pour mesurer la consistance
        for llm_name, test_method in [("Gemini", self.test_gemini_test_generation), 
                                     ("DeepSeek", self.test_deepseek_test_generation),
                                     ("Mistral", self.test_mistral_generation)]:
            
            llm_results = []
            quality_scores = []
            
            for i in range(5):
                result = await test_method(baseline_api)
                result.test_name = f"Pipeline-Consistency-{llm_name}-Run{i+1}"
                
                if result.success:
                    quality_scores.append(result.quality_score)
                    llm_results.append(result)
                
                await asyncio.sleep(1)  # Éviter la surcharge
            
            # Analyser la consistance
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                quality_variance = sum((score - avg_quality) ** 2 for score in quality_scores) / len(quality_scores)
                consistency_score = max(0, 100 - (quality_variance * 10))  # Plus la variance est faible, plus la consistance est élevée
                
                # Stocker dans les métriques pipeline
                self.pipeline_metrics["generation_consistency"][llm_name] = {
                    "avg_quality": avg_quality,
                    "quality_variance": quality_variance,
                    "consistency_score": consistency_score,
                    "success_rate": len(llm_results) / 5
                }
                
                consistency_results.extend(llm_results)
        
        return consistency_results
    
    async def test_snippet_complexity_scaling(self) -> List[TestResult]:
        """Test pour évaluer comment le pipeline gère différents niveaux de complexité"""
        complexity_results = []
        
        # Snippets de complexité croissante
        complexity_samples = [
            {
                "name": "Simple-Single-Endpoint",
                "complexity": "simple",
                "code": """
@RestController
public class SimpleController {
    @GetMapping("/health")
    public String health() {
        return "OK";
    }
}
"""
            },
            {
                "name": "Medium-CRUD-Operations", 
                "complexity": "medium",
                "code": """
@RestController
@RequestMapping("/api/products")
public class ProductController {
    
    @GetMapping
    public List<Product> getAllProducts() {
        return productService.findAll();
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<Product> getProduct(@PathVariable Long id) {
        Product product = productService.findById(id);
        return product != null ? ResponseEntity.ok(product) : ResponseEntity.notFound().build();
    }
    
    @PostMapping
    public ResponseEntity<Product> createProduct(@Valid @RequestBody Product product) {
        Product created = productService.save(product);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }
}
"""
            },
            {
                "name": "Complex-Business-Logic",
                "complexity": "complex", 
                "code": """
@RestController
@RequestMapping("/api/orders")
@Validated
@Transactional
public class OrderController {
    
    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
            @Valid @RequestBody CreateOrderRequest request,
            @RequestHeader("User-Id") String userId,
            Authentication auth) {
        
        try {
            // Validate inventory
            if (!inventoryService.checkAvailability(request.getItems())) {
                throw new InsufficientStockException("Items not available");
            }
            
            // Calculate pricing with discounts
            BigDecimal total = pricingService.calculateTotal(request.getItems(), request.getCouponCode());
            
            // Process payment
            PaymentResult payment = paymentService.charge(request.getPaymentMethod(), total);
            if (!payment.isSuccessful()) {
                return ResponseEntity.status(HttpStatus.PAYMENT_REQUIRED).build();
            }
            
            // Create order
            Order order = orderService.createOrder(userId, request.getItems(), total, payment.getTransactionId());
            
            // Send notifications
            notificationService.sendOrderConfirmation(order);
            
            return ResponseEntity.status(HttpStatus.CREATED).body(OrderResponse.from(order));
            
        } catch (InsufficientStockException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(new ErrorResponse("INSUFFICIENT_STOCK", e.getMessage()));
        } catch (PaymentProcessingException e) {
            return ResponseEntity.status(HttpStatus.PAYMENT_REQUIRED)
                .body(new ErrorResponse("PAYMENT_FAILED", "Payment processing failed"));
        }
    }
}
"""
            }
        ]
        
        # Tester chaque niveau de complexité avec Gemini (référence)
        for sample in complexity_samples:
            result = await self.test_gemini_test_generation(sample)
            result.test_name = f"Pipeline-Complexity-{sample['complexity'].title()}"
            
            # Stocker les métriques de gestion de complexité
            complexity_level = sample["complexity"]
            if complexity_level not in self.pipeline_metrics["snippet_complexity_handling"]:
                self.pipeline_metrics["snippet_complexity_handling"][complexity_level] = []
            
            self.pipeline_metrics["snippet_complexity_handling"][complexity_level].append({
                "quality_score": result.quality_score if result.success else 0,
                "success": result.success,
                "response_time": result.response_time,
                "code_length": len(sample["code"])
            })
            
            complexity_results.append(result)
            await asyncio.sleep(2)  # Pause entre les tests
            
        return complexity_results
    
    def calculate_system_metrics(self):
        """Calcule les métriques globales du système et du pipeline"""
        if not self.test_results:
            return
        
        self.system_metrics.total_tests = len(self.test_results)
        self.system_metrics.successful_tests = sum(1 for r in self.test_results if r.success)
        self.system_metrics.failed_tests = self.system_metrics.total_tests - self.system_metrics.successful_tests
        
        if self.system_metrics.total_tests > 0:
            self.system_metrics.success_rate = (self.system_metrics.successful_tests / self.system_metrics.total_tests) * 100
        
        # Calcul des temps moyens
        response_times = [r.response_time for r in self.test_results if r.success]
        execution_times = [r.execution_time for r in self.test_results if r.success]
        quality_scores = [r.quality_score for r in self.test_results if r.success and r.quality_score > 0]
        
        if response_times:
            self.system_metrics.avg_response_time = statistics.mean(response_times)
        if execution_times:
            self.system_metrics.avg_execution_time = statistics.mean(execution_times)
        if quality_scores:
            self.system_metrics.avg_quality_score = statistics.mean(quality_scores)
        
        # Analyse de couverture
        coverage_metrics = [r.coverage_metrics for r in self.test_results if r.coverage_metrics]
        if coverage_metrics:
            self.system_metrics.coverage_analysis = self._analyze_coverage_metrics(coverage_metrics)
        
        # Calculs spécifiques au pipeline de génération
        self._calculate_pipeline_performance_metrics()
    
    def _calculate_pipeline_performance_metrics(self):
        """Calcule les métriques de performance spécifiques au pipeline"""
        
        # Calculer les performances moyennes par LLM
        for llm_name, scores in self.pipeline_metrics["llm_quality_scores"].items():
            if scores:
                avg_score = sum(scores) / len(scores)
                min_score = min(scores)
                max_score = max(scores)
                score_variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
                
                print(f"\n*** Metriques LLM - {llm_name}: ***")
                print(f"   Score qualité moyen: {avg_score:.2f}/100")
                print(f"   Score minimum: {min_score:.2f}")
                print(f"   Score maximum: {max_score:.2f}")
                print(f"   Variance: {score_variance:.2f} (plus c'est bas, plus c'est consistant)")
        
        # Analyser la gestion de complexité
        if self.pipeline_metrics["snippet_complexity_handling"]:
            print(f"\n🔧 Gestion de la complexité des snippets:")
            for complexity, metrics_list in self.pipeline_metrics["snippet_complexity_handling"].items():
                if metrics_list:
                    avg_quality = sum(m["quality_score"] for m in metrics_list) / len(metrics_list)
                    success_rate = sum(1 for m in metrics_list if m["success"]) / len(metrics_list) * 100
                    avg_time = sum(m["response_time"] for m in metrics_list) / len(metrics_list)
                    
                    print(f"   {complexity.capitalize()}: Qualité {avg_quality:.2f}, Succès {success_rate:.1f}%, Temps {avg_time:.2f}s")
        
        # Analyser la consistance de génération
        if self.pipeline_metrics["generation_consistency"]:
            print(f"\n🎯 Consistance de génération:")
            for llm_name, consistency_data in self.pipeline_metrics["generation_consistency"].items():
                print(f"   {llm_name}: Score consistance {consistency_data['consistency_score']:.2f}/100, Succès {consistency_data['success_rate']*100:.1f}%")
    
    def _analyze_coverage_metrics(self, coverage_list: List[Dict]) -> Dict:
        """Analyse les métriques de couverture collectées"""
        analysis = {
            "total_executions": len(coverage_list),
            "avg_line_coverage": 0.0,
            "avg_branch_coverage": 0.0,
            "quality_distribution": {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        }
        
        line_coverages = []
        branch_coverages = []
        
        for metrics in coverage_list:
            if "line_coverage" in metrics:
                line_coverages.append(metrics["line_coverage"])
            if "branch_coverage" in metrics:
                branch_coverages.append(metrics["branch_coverage"])
            
            # Classification de la qualité
            line_cov = metrics.get("line_coverage", 0)
            branch_cov = metrics.get("branch_coverage", 0)
            
            if line_cov >= 90 and branch_cov >= 85:
                analysis["quality_distribution"]["excellent"] += 1
            elif line_cov >= 80 and branch_cov >= 70:
                analysis["quality_distribution"]["good"] += 1
            elif line_cov >= 60 and branch_cov >= 50:
                analysis["quality_distribution"]["fair"] += 1
            else:
                analysis["quality_distribution"]["poor"] += 1
        
        if line_coverages:
            analysis["avg_line_coverage"] = statistics.mean(line_coverages)
        if branch_coverages:
            analysis["avg_branch_coverage"] = statistics.mean(branch_coverages)
        
        return analysis
    
    def generate_report(self) -> str:
        """Génère un rapport détaillé focalisé sur l'évaluation du pipeline de génération"""
        report = []
        report.append("=" * 90)
        report.append("*** RAPPORT D'EVALUATION DU PIPELINE GEMINI DE GENERATION DE TESTS IA ***")
        report.append("=" * 90)
        report.append("")
        report.append(f"*** Date d'evaluation Gemini: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ***")
        report.append("*** Focus: Evaluation de la qualite Gemini et performance du pipeline ***")
        report.append("")
        
        # Détection mode massif
        massive_mode = "--massive" in sys.argv
        total_generations = sum(len(scores) for scores in self.pipeline_metrics["llm_quality_scores"].values())
        
        # Métriques spécifiques au pipeline
        if massive_mode:
            report.append("*** RESULTATS EVALUATION MASSIVE DU PIPELINE ***")
            report.append("-" * 60)
            report.append(f"Mode d'evaluation: MASSIF GEMINI ({MASSIVE_TEST_CONFIG['tests_per_llm']} tests)")
            report.append(f"Total générations testées: {total_generations}")
            report.append(f"Durée totale d'évaluation: {self.system_metrics.total_execution_time:.1f}s")
            report.append(f"Débit de génération: {total_generations / max(self.system_metrics.total_execution_time, 1):.2f} tests/sec")
        else:
            report.append("*** PERFORMANCE GLOBALE DU PIPELINE GEMINI ***")
            report.append("-" * 50)
            
        report.append(f"Tests de génération exécutés: {self.system_metrics.total_tests}")
        report.append(f"Générations réussies: {self.system_metrics.successful_tests}")
        report.append(f"Taux de succès du pipeline: {self.system_metrics.success_rate:.2f}%")
        report.append(f"Qualité moyenne des tests générés: {self.system_metrics.avg_quality_score:.2f}/100")
        report.append(f"Temps moyen de génération: {self.system_metrics.avg_response_time:.3f}s")
        
        if massive_mode:
            report.append(f"Echantillons d'API testes avec Gemini: {len(API_SAMPLES)}")
            report.append(f"Variations Gemini par echantillon: {total_generations // len(API_SAMPLES):.1f}")
            
            # Statistiques de charge
            if self.system_metrics.avg_response_time > 0:
                theoretical_max = 3600 / self.system_metrics.avg_response_time  # tests/heure
                actual_throughput = total_generations / (self.system_metrics.total_execution_time / 3600)
                efficiency = (actual_throughput / theoretical_max) * 100 if theoretical_max > 0 else 0
                report.append(f"Efficacité du pipeline: {efficiency:.1f}% du débit théorique maximum")
        
        # Évaluation par LLM
        report.append("")
        report.append("*** ANALYSE DE PERFORMANCE GEMINI ***")
        report.append("-" * 40)
        
        for llm_name, scores in self.pipeline_metrics["llm_quality_scores"].items():
            if scores:
                avg_score = sum(scores) / len(scores)
                min_score = min(scores)
                max_score = max(scores)
                consistency = max_score - min_score  # Écart pour mesurer la consistance
                
                report.append(f"{llm_name}:")
                report.append(f"  - Score qualité moyen: {avg_score:.2f}/100")
                report.append(f"  - Plage de scores: {min_score:.1f} - {max_score:.1f}")
                report.append(f"  - Consistance (écart): {consistency:.1f} (plus bas = plus consistant)")
                report.append(f"  - Nombre de générations: {len(scores)}")
                
                # Recommandation basée sur la performance
                if avg_score >= 80:
                    recommendation = "🌟 Excellent - Recommandé pour production"
                elif avg_score >= 70:
                    recommendation = "✅ Bon - Utilisable avec optimisations"
                elif avg_score >= 60:
                    recommendation = "⚠️ Moyen - Nécessite amélioration des prompts"
                else:
                    recommendation = "*** FAIBLE - Revision majeure necessaire ***"
                    
                report.append(f"  - Recommandation: {recommendation}")
                report.append("")
        
        # Analyse de performance par catégorie
        report.append("*** ANALYSE DE PERFORMANCE GEMINI PAR CATEGORIE ***")
        report.append("-" * 50)
        
        categories = {}
        for result in self.test_results:
            if "Gemini" in result.test_name:
                category = "Gemini AI"
            elif "DeepSeek" in result.test_name:
                category = "DeepSeek (Ollama)"
            elif "Mistral" in result.test_name:
                category = "Mistral AI"
            elif "Concurrent" in result.test_name:
                category = "Tests Concurrents"
            elif "Stress" in result.test_name:
                category = "Tests de Charge"
            elif "Edge Case" in result.test_name:
                category = "Cas Limites"
            elif "Execution with Metrics" in result.test_name:
                category = "Exécution avec Métriques"
            else:
                category = "Autres"
            
            if category not in categories:
                categories[category] = {"success": 0, "total": 0, "avg_time": []}
            
            categories[category]["total"] += 1
            if result.success:
                categories[category]["success"] += 1
                categories[category]["avg_time"].append(result.response_time)
        
        for category, stats in categories.items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            avg_time = statistics.mean(stats["avg_time"]) if stats["avg_time"] else 0
            
            report.append(f"{category}:")
            report.append(f"  - Succès: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
            report.append(f"  - Temps moyen: {avg_time:.3f}s")
            report.append("")
        
        # Analyse de la couverture de code
        if self.system_metrics.coverage_analysis:
            report.append("ANALYSE DE LA COUVERTURE DE CODE")
            report.append("-" * 40)
            cov = self.system_metrics.coverage_analysis
            report.append(f"Exécutions avec métriques: {cov['total_executions']}")
            report.append(f"Couverture de ligne moyenne: {cov['avg_line_coverage']:.1f}%")
            report.append(f"Couverture de branche moyenne: {cov['avg_branch_coverage']:.1f}%")
            report.append("")
            report.append("Distribution de qualité:")
            for quality, count in cov['quality_distribution'].items():
                report.append(f"  - {quality.capitalize()}: {count}")
            report.append("")
        
        # Tests échoués détaillés
        failed_tests = [r for r in self.test_results if not r.success]
        if failed_tests:
            report.append("*** DETAILS DES ECHECS ***")
            report.append("-" * 30)
            for test in failed_tests[:10]:  # Limiter à 10 échecs
                report.append(f"Test: {test.test_name}")
                report.append(f"  Erreur: {test.error_message}")
                report.append(f"  Status: {test.response_status}")
                report.append("")
        
        # Recommandations
        report.append("*** RECOMMANDATIONS POUR L'AMELIORATION GEMINI ***")
        report.append("-" * 45)
        
        if self.system_metrics.success_rate < 80:
            report.append("*** Taux de succes faible - verifier la stabilite du service Gemini ***")
        
        if self.system_metrics.avg_response_time > 5.0:
            report.append("⚠️  Temps de réponse élevé - optimiser les performances")
        
        if self.system_metrics.avg_quality_score < 70:
            report.append("*** Qualite des tests generes faible - ameliorer les prompts Gemini ***")
        
        if len([r for r in self.test_results if "Edge Case" in r.test_name and not r.success]) > 2:
            report.append("⚠️  Gestion des cas limites à améliorer")
        
        report.append("")
        report.append("*** Tests Gemini completes avec succes! ***")
        report.append("*** Voir le fichier test_results.json pour les donnees detaillees ***")
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_detailed_results(self, filename: str = "pipeline_evaluation_results.json"):
        """Sauvegarde les résultats optimisés pour le suivi d'amélioration du pipeline"""
        
        # Calculer les métriques de tendance si des résultats précédents existent
        historical_comparison = self._load_historical_data(filename)
        
        pipeline_results = {
            "evaluation_metadata": {
                "test_date": datetime.now().isoformat(),
                "test_version": "2.0-pipeline-focused",
                "total_pipeline_tests": len(self.test_results),
                "test_duration_seconds": sum(r.execution_time for r in self.test_results),
                "focus": "LLM quality and generation pipeline performance"
            },
            
            "pipeline_performance": {
                "overall_success_rate": self.system_metrics.success_rate,
                "avg_generation_time": self.system_metrics.avg_response_time,
                "avg_quality_score": self.system_metrics.avg_quality_score,
                "total_generations": self.system_metrics.total_tests
            },
            
            "llm_comparative_analysis": self.pipeline_metrics["llm_quality_scores"],
            
            "consistency_metrics": self.pipeline_metrics["generation_consistency"],
            
            "complexity_handling": self.pipeline_metrics["snippet_complexity_handling"],
            
            "improvement_tracking": {
                "current_session_summary": {
                    "best_performing_llm": self._identify_best_llm(),
                    "most_consistent_llm": self._identify_most_consistent_llm(),
                    "areas_for_improvement": self._identify_improvement_areas()
                },
                "historical_comparison": historical_comparison
            },
            
            "raw_test_results": [r.to_dict() for r in self.test_results if "Pipeline-" in r.test_name]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(pipeline_results, f, indent=2, ensure_ascii=False)
        
        # Aussi sauvegarder un résumé CSV pour suivi facile
        self._save_tracking_csv()
        
        logger.info(f"*** Resultats d'evaluation pipeline sauvegardes dans {filename} ***")
        logger.info("*** Resume de suivi sauvegarde dans pipeline_tracking.csv ***")
    
    def _load_historical_data(self, filename: str) -> Dict[str, Any]:
        """Charge les données historiques pour comparaison"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                previous_data = json.load(f)
                
            if "pipeline_performance" in previous_data:
                return {
                    "previous_test_date": previous_data["evaluation_metadata"].get("test_date"),
                    "quality_improvement": self.system_metrics.avg_quality_score - 
                                         previous_data["pipeline_performance"].get("avg_quality_score", 0),
                    "speed_improvement": previous_data["pipeline_performance"].get("avg_generation_time", 0) - 
                                       self.system_metrics.avg_response_time,
                    "success_rate_change": self.system_metrics.success_rate - 
                                         previous_data["pipeline_performance"].get("overall_success_rate", 0)
                }
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return {"note": "Première exécution - pas de données historiques"}
        
        return {}
    
    def _identify_best_llm(self) -> str:
        """Identifie le LLM avec les meilleures performances globales"""
        best_llm = "N/A"
        best_score = 0
        
        for llm_name, scores in self.pipeline_metrics["llm_quality_scores"].items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score > best_score:
                    best_score = avg_score
                    best_llm = f"{llm_name} ({avg_score:.2f}/100)"
        
        return best_llm
    
    def _identify_most_consistent_llm(self) -> str:
        """Identifie le LLM le plus consistant"""
        most_consistent = "N/A"
        lowest_variance = float('inf')
        
        for llm_name, consistency_data in self.pipeline_metrics["generation_consistency"].items():
            variance = consistency_data.get("quality_variance", float('inf'))
            if variance < lowest_variance:
                lowest_variance = variance
                most_consistent = f"{llm_name} (variance: {variance:.2f})"
        
        return most_consistent
    
    def _identify_improvement_areas(self) -> List[str]:
        """Identifie les domaines nécessitant amélioration"""
        improvements = []
        
        # Analyser les scores moyens
        for llm_name, scores in self.pipeline_metrics["llm_quality_scores"].items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score < 70:
                    improvements.append(f"Améliorer la qualité des prompts pour {llm_name} (score: {avg_score:.1f})")
        
        # Analyser la consistance
        for llm_name, consistency_data in self.pipeline_metrics["generation_consistency"].items():
            if consistency_data.get("consistency_score", 0) < 80:
                improvements.append(f"Améliorer la consistance de {llm_name}")
        
        # Analyser la gestion de complexité
        for complexity, metrics_list in self.pipeline_metrics["snippet_complexity_handling"].items():
            if metrics_list:
                avg_quality = sum(m["quality_score"] for m in metrics_list) / len(metrics_list)
                if avg_quality < 60:
                    improvements.append(f"Améliorer la gestion des snippets {complexity}")
        
        if not improvements:
            improvements.append("Pipeline performant - continuer l'optimisation fine")
        
        return improvements
    
    def _save_tracking_csv(self):
        """Sauvegarde un CSV simple pour le suivi des améliorations"""
        import csv
        from pathlib import Path
        
        csv_file = Path("pipeline_tracking.csv")
        
        # Créer l'en-tête si le fichier n'existe pas
        write_header = not csv_file.exists()
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    "Date", "Overall_Success_Rate", "Avg_Quality_Score", "Avg_Generation_Time",
                    "Gemini_Avg_Quality", "DeepSeek_Avg_Quality", "Mistral_Avg_Quality",
                    "Best_LLM", "Most_Consistent_LLM", "Total_Tests"
                ])
            
            # Calculer les moyennes par LLM
            gemini_avg = sum(self.pipeline_metrics["llm_quality_scores"].get("Gemini", [0])) / max(1, len(self.pipeline_metrics["llm_quality_scores"].get("Gemini", [0])))
            deepseek_avg = sum(self.pipeline_metrics["llm_quality_scores"].get("DeepSeek", [0])) / max(1, len(self.pipeline_metrics["llm_quality_scores"].get("DeepSeek", [0])))
            mistral_avg = sum(self.pipeline_metrics["llm_quality_scores"].get("Mistral", [0])) / max(1, len(self.pipeline_metrics["llm_quality_scores"].get("Mistral", [0])))
            
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                f"{self.system_metrics.success_rate:.2f}",
                f"{self.system_metrics.avg_quality_score:.2f}",
                f"{self.system_metrics.avg_response_time:.3f}",
                f"{gemini_avg:.2f}",
                f"{deepseek_avg:.2f}",
                f"{mistral_avg:.2f}",
                self._identify_best_llm().split(' ')[0],  # Juste le nom
                self._identify_most_consistent_llm().split(' ')[0],  # Juste le nom
                self.system_metrics.total_tests
            ])
    
    async def run_comprehensive_tests(self):
        """Lance tous les tests du prototype - version allégée ou massive selon les arguments"""
        
        # Vérifier si mode massif demandé
        massive_mode = "--massive" in sys.argv or len(sys.argv) > 1 and "massive" in sys.argv[1].lower()
        
        if massive_mode:
            logger.info("*** DEMARRAGE TESTS MASSIFS GEMINI - EVALUATION INTENSIVE ***")
            logger.info(f"*** Configuration: {MASSIVE_TEST_CONFIG['tests_per_llm']} tests pour Gemini ***")
            logger.info(f"*** Duree estimee: {(MASSIVE_TEST_CONFIG['tests_per_llm'] * MASSIVE_TEST_CONFIG['timeout_per_test']) // 60} minutes ***")
            await self.run_massive_pipeline_tests()
        else:
            logger.info("*** Debut des tests comprehensifs du prototype d'IA (mode standard) ***")
            await self.run_standard_tests()
    
    async def run_massive_pipeline_tests(self):
        """Lance des centaines de tests pour évaluation intensive du pipeline"""
        await self.setup_session()
        
        try:
            # 1. Test de santé préliminaire
            logger.info("[1] Verification sante du systeme...")
            health_result = await self.test_backend_health()
            self.test_results.append(health_result)
            
            if not health_result.success:
                logger.error("*** Systeme non disponible - arret des tests massifs ***")
                return
            
            # 2. TESTS MASSIFS - GEMINI UNIQUEMENT
            llms = [
                ("Gemini", self.test_gemini_test_generation)
            ]
            
            total_tests = MASSIVE_TEST_CONFIG['tests_per_llm'] * len(llms)
            current_test = 0
            
            for llm_name, test_func in llms:
                logger.info(f"*** TESTS MASSIFS {llm_name.upper()} - {MASSIVE_TEST_CONFIG['tests_per_llm']} tests ***")
                
                # Diviser en batches pour éviter surcharge
                batch_size = MASSIVE_TEST_CONFIG['batch_size']
                total_batches = (MASSIVE_TEST_CONFIG['tests_per_llm'] + batch_size - 1) // batch_size
                
                for batch_num in range(total_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min(start_idx + batch_size, MASSIVE_TEST_CONFIG['tests_per_llm'])
                    batch_tests = end_idx - start_idx
                    
                    logger.info(f"   >>> Batch {batch_num + 1}/{total_batches} - {batch_tests} tests")
                    
                    # Tests concurrents dans le batch
                    batch_tasks = []
                    for i in range(start_idx, end_idx):
                        # Sélectionner échantillon d'API de manière cyclique
                        api_sample = API_SAMPLES[i % len(API_SAMPLES)]
                        
                        # Créer tâche asynchrone
                        task = self._run_single_massive_test(test_func, api_sample, llm_name, current_test + i - start_idx + 1, total_tests)
                        batch_tasks.append(task)
                    
                    # Exécuter batch avec limite de concurrence
                    semaphore = asyncio.Semaphore(MASSIVE_TEST_CONFIG['max_concurrent'])
                    batch_results = await asyncio.gather(*[self._run_with_semaphore(semaphore, task) for task in batch_tasks], return_exceptions=True)
                    
                    # Traiter résultats du batch
                    for result in batch_results:
                        if isinstance(result, TestResult):
                            self.test_results.append(result)
                        elif isinstance(result, Exception):
                            logger.error(f"Erreur dans batch: {result}")
                    
                    current_test += batch_tests
                    
                    # Pause entre batches
                    if batch_num < total_batches - 1:
                        logger.info(f"   ... Pause {MASSIVE_TEST_CONFIG['delay_between_batches']}s entre batches...")
                        await asyncio.sleep(MASSIVE_TEST_CONFIG['delay_between_batches'])
                
                logger.info(f"*** {llm_name} TERMINE - {MASSIVE_TEST_CONFIG['tests_per_llm']} tests executes ***")
            
            # 3. Tests de consistance sur echantillon reduit
            logger.info("[3] Tests de consistance du pipeline (echantillon)...")
            consistency_results = await self.test_pipeline_consistency()
            self.test_results.extend(consistency_results)
            
            logger.info(f"*** TESTS MASSIFS TERMINES - {len(self.test_results)} tests executes ***")
            
        finally:
            await self.cleanup_session()
    
    async def _run_single_massive_test(self, test_func, api_sample, llm_name, test_num, total_tests):
        """Exécute un test individuel dans la suite massive"""
        try:
            # Afficher progrès périodiquement  
            if test_num % 20 == 0 or test_num <= 5:
                progress = (test_num / total_tests) * 100
                logger.info(f"   >>> Progres: {test_num}/{total_tests} ({progress:.1f}%) - {llm_name}")
            
            result = await test_func(api_sample)
            return result
            
        except Exception as e:
            logger.warning(f"Erreur test {test_num} ({llm_name}): {str(e)[:100]}")
            return TestResult(
                test_name=f"Massive-{llm_name}-{test_num}",
                success=False,
                execution_time=0,
                response_time=0,
                response_status=0,
                response_size=0,
                error_message=str(e)
            )
    
    async def _run_with_semaphore(self, semaphore, coro):
        """Exécute une coroutine avec limite de concurrence"""
        async with semaphore:
            return await coro
    
    async def run_standard_tests(self):
        """Lance les tests standard (mode original)"""
        await self.setup_session()
        
        try:
            # 1. Test de santé du backend
            logger.info("[1] Test de sante du backend...")
            health_result = await self.test_backend_health()
            self.test_results.append(health_result)
            
            # 2. Tests de génération avec échantillons sélectionnés
            logger.info("[2] Tests de generation avec tous les modeles IA...")
            selected_samples = API_SAMPLES[:10]  # Limiter en mode standard
            
            for i, api_sample in enumerate(selected_samples, 1):
                logger.info(f"   Testant échantillon {i}/{len(selected_samples)}: {api_sample['name']}")
                
                # Test Gemini
                gemini_result = await self.test_gemini_test_generation(api_sample)
                self.test_results.append(gemini_result)
                
                # Test DeepSeek
                deepseek_result = await self.test_deepseek_test_generation(api_sample)
                self.test_results.append(deepseek_result)
                
                # Test Mistral
                mistral_result = await self.test_mistral_generation(api_sample)
                self.test_results.append(mistral_result)
                
                # Pause entre les échantillons
                await asyncio.sleep(1)
            
            # 3. Tests d'exécution avec métriques (échantillon réduit)
            logger.info("[3] Tests d'execution avec metriques de couverture...")
            for api_sample in selected_samples[:3]:  # Tester sur 3 échantillons
                execution_result = await self.test_execution_with_metrics(api_sample)
                self.test_results.append(execution_result)
                await asyncio.sleep(2)  # Attente pour l'exécution
            
            # 4. Tests spécifiques au pipeline de génération
            logger.info("[4] Tests de consistance du pipeline...")
            consistency_results = await self.test_pipeline_consistency()
            self.test_results.extend(consistency_results)
            
            # 5. Tests de montée en complexité des snippets
            logger.info("[5] Tests de gestion de complexite des snippets...")
            complexity_results = await self.test_snippet_complexity_scaling()
            self.test_results.extend(complexity_results)
            
            # 6. Calcul des métriques finales avec focus pipeline
            logger.info("[6] Calcul des metriques du pipeline...")
            self.calculate_system_metrics()
            
        finally:
            await self.cleanup_session()
        
        logger.info("*** Tests termines! ***")

async def main():
    """Fonction principale - Focus évaluation du pipeline de génération"""
    import sys
    
    # Vérifier les modes demandés
    quick_mode = "--quick" in sys.argv
    massive_mode = "--massive" in sys.argv
    
    if massive_mode:
        print("*** EVALUATEUR DE PIPELINE - MODE MASSIF GEMINI ***")
        print("=" * 60)
        print("*** TESTS INTENSIFS GEMINI UNIQUEMENT ***")
        print(f"* {MASSIVE_TEST_CONFIG['tests_per_llm']} tests pour GEMINI uniquement")
        print(f"* Total: {MASSIVE_TEST_CONFIG['tests_per_llm']} tests de generation")
        print(f"* Duree estimee: {(MASSIVE_TEST_CONFIG['tests_per_llm'] * MASSIVE_TEST_CONFIG['timeout_per_test']) // 60} à {(MASSIVE_TEST_CONFIG['tests_per_llm'] * MASSIVE_TEST_CONFIG['timeout_per_test']) // 40} minutes")
        print(f"* Concurrence: {MASSIVE_TEST_CONFIG['max_concurrent']} requetes simultanees")
        print(f"* Batches: {MASSIVE_TEST_CONFIG['batch_size']} tests par batch")
        print()
        print("*** ATTENTION: Ce mode sollicitera intensivement l'API Gemini! ***")
        
    elif quick_mode:
        print("*** EVALUATEUR DE PIPELINE - MODE RAPIDE ***")
        print("=" * 50)
        print("*** Tests reduits pour un apercu rapide du pipeline ***")
        print("* Gemini teste sur 10 echantillons")
        print("* Duree estimee: 2-3 minutes")
    else:
        print("*** EVALUATEUR DE PIPELINE - GENERATION DE TESTS IA ***")
        print("=" * 80)
        print("*** Ce script evalue specifiquement votre pipeline de generation: ***")
        print("* Qualite de Gemini")
        print("* Consistance de generation pour les snippets de code")
        print("* Gestion de la complexite des APIs")
        print("* Metriques d'amelioration continue")
        print("* Rapport de recommandations")
        print()
        print("*** Modes disponibles: ***")
        print("   python comprehensive_test_suite.py --quick     (mode rapide)")
        print("   python comprehensive_test_suite.py --massive   (tests intensifs)")
        print("   python comprehensive_test_suite.py             (mode standard)")
    
    print()
    print("*** Utilisez ces resultats pour optimiser votre implementation! ***")
    print()
    
    # Vérifier que les services sont démarrés
    print("*** PREREQUIS POUR L'EVALUATION:")
    print("* Backend Flask (Gemini) sur http://localhost:5000")
    print("* Cles API Gemini configurees (GEMINI_API_KEY)")
    print("* Mode: Tests massifs Gemini uniquement")
    print()
    
    response = input("Vos services de génération sont-ils prêts? (y/N): ").strip().lower()
    if response != 'y':
        print("*** Demarrez vos services de generation avant de continuer. ***")
        print("*** Conseil: Lancez check_services.py pour verifier l'etat ***")
        sys.exit(1)
    
    # Lancer l'évaluation du pipeline
    tester = AutoTestPrototypeTester()
    
    # Configurer les paramètres selon le mode
    if quick_mode:
        tester.config.samples_per_complexity = 2  # Réduire les échantillons
        tester.config.consistency_test_count = 2  # Moins de tests de consistance
        print("⚡ Mode rapide: paramètres optimisés pour tests rapides")
    
    try:
        print("\n*** Demarrage de l'evaluation du pipeline Gemini...")
        
        # Exécuter l'évaluation focalisée sur le pipeline
        await tester.run_comprehensive_tests()
        
        # Générer et afficher le rapport d'évaluation
        report = tester.generate_report()
        print("\n")
        print(report)
        
        # Sauvegarder les résultats pour suivi d'amélioration
        tester.save_detailed_results()
        
        # Évaluation finale du pipeline
        quality_score = tester.system_metrics.avg_quality_score
        success_rate = tester.system_metrics.success_rate
        
        print("\n" + "="*60)
        print("*** EVALUATION FINALE DU PIPELINE ***")
        print("="*60)
        
        if quality_score >= 80 and success_rate >= 90:
            print("� EXCELLENT PIPELINE! Prêt pour la production")
            print("   → Continuez l'optimisation fine")
        elif quality_score >= 70 and success_rate >= 80:
            print("✅ BON PIPELINE! Quelques améliorations recommandées")
            print("   → Focalisez sur la consistance et cas limites")
        elif quality_score >= 60 and success_rate >= 70:
            print("⚠️  PIPELINE MOYEN! Améliorations nécessaires")
            print("   → Revisitez vos prompts et gestion d'erreurs")
        else:
            print("*** PIPELINE PERFECTIBLE! Revision majeure recommandee ***")
            print("   → Analysez les métriques détaillées pour prioriser")
        
        print(f"\n� Scores finaux:")
        print(f"   • Taux de succès: {success_rate:.1f}%")
        print(f"   • Qualité moyenne: {quality_score:.1f}/100")
        print(f"   • Tests évalués: {len(tester.test_results)}")
        
        print("\n*** Resultats sauvegardes:")
        print(f"   • pipeline_evaluation_results.json - Données complètes")
        print(f"   • pipeline_tracking.csv - Suivi historique")
        print(f"   • test_results.log - Logs détaillés")
        
        print("\n*** Prochaines etapes:")
        print(f"   1. Analysez les recommandations dans le rapport JSON")
        print(f"   2. Implémentez les améliorations suggérées")
        print(f"   3. Relancez ce script pour mesurer les progrès")
        print(f"   4. Consultez pipeline_tracking.csv pour voir les tendances")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Évaluation interrompue par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation: {e}")
        print(f"\n*** Erreur d'evaluation: {e} ***")
        print("*** Verifiez que tous vos services de generation sont accessibles ***")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())