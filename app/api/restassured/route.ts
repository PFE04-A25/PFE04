import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();

    if (!body.api_code) {
      return NextResponse.json(
        { error: "Missing api_code parameter" },
        { status: 400 },
      );
    }

    const baseUrl = process.env.BACKEND_BASE_URL || "http://localhost:5000";
    const apiUrl = `${baseUrl}/rest-assured-test/gemini`;

    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ api_code: body.api_code }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Server error: ${errorText}` },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
