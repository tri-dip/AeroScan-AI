import { ScanApiResponse } from "./types";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  ""
);

export class ScanApiError extends Error {}

export async function scanDocument(
  documentFile: File | Blob,
  selfieFile: File | Blob
): Promise<ScanApiResponse> {
  const formData = new FormData();
  formData.append(
    "file",
    documentFile,
    documentFile instanceof File ? documentFile.name : "document.jpg"
  );
  formData.append(
    "selfie",
    selfieFile,
    selfieFile instanceof File ? selfieFile.name : "selfie.jpg"
  );

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/scan/`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new ScanApiError(
      `Could not reach the screening backend at ${API_BASE_URL}. Confirm it is running.`
    );
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // Non-JSON error body - fall back to the status text.
    }
    throw new ScanApiError(detail);
  }

  return response.json();
}
