"use server";

import { connectToDB } from "../mongoose";
import TestCase from "@/lib/models/testcase.model";

interface Params {
  testType: string;
  sourceCode: string;
  testCase: string;
}

export async function createTestCase({
  testType,
  sourceCode,
  testCase,
}: Params) {
  try {
    const baseUrl = process.env.BACKEND_BASE_URL || "http://127.0.0.1:5000"; // Adjust as needed (http://127.0.0.1:5000)
    
    const response = await fetch(`${baseUrl}/db/testcases`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        testType,
        sourceCode,
        testCase,
      }),
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error: unknown) {
    console.error("Error saving to database:", error);
    throw new Error(`Failed to create test case: ${error}`);
  }
}
