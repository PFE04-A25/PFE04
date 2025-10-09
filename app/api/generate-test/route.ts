import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    console.log("Request received with API code");

    if (!body.api_code) {
      return NextResponse.json(
        { error: "Missing api_code parameter" },
        { status: 400 },
      );
    }
    // Get the test type from the request body
    const testType = body.testType;
    console.log(`Generating ${testType} tests`);

    const baseUrl = process.env.BACKEND_BASE_URL || "http://localhost:5000";
    // Choose the API endpoint based on the test type
    let apiUrl;
    switch (testType) {
      case "unit":
        apiUrl = `${baseUrl}/unit-test/gemini`;
        break;
      case "restassured":
        apiUrl = `${baseUrl}/rest-assured-test/gemini`;
        break;
      default:
        apiUrl = `${baseUrl}/rest-assured-test/gemini`;
        break;
    }
    
    console.log(`Making request to: ${apiUrl}`);


    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ api_code: body.api_code }),
    });
    console.log(`Response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Error response from backend: ${errorText}`);
      return NextResponse.json(
        { error: `Server error: ${errorText}` },
        { status: response.status },
      );
    }

    const data = await response.json();
    console.log("Response data:", {
      hasGeneratedTest: !!data.generated_test,
      generatedTestLength: data.generated_test?.length || 0,
      // Only log the first few lines for brevity
      testPreview: data.generated_test?.split('\n').slice(0, 5).join('\n') + '...'
    });
    
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
