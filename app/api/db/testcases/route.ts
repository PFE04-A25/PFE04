import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    console.log("Sending test case to database");

    const baseUrl = process.env.BACKEND_BASE_URL || "http://localhost:5000";
    const apiUrl = `${baseUrl}/db/testcases`;
    
    console.log(`Making request to: ${apiUrl}`);

    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        testType: body.testType,
        sourceCode: body.sourceCode,
        testCase: body.testCase,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Error response from backend: ${errorText}`);
      return NextResponse.json(
        { error: `Database error: ${errorText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log("Database operation successful", data);
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error:", error);
    return NextResponse.json(
      { error: "Failed to save to database" },
      { status: 500 }
    );
  }
}