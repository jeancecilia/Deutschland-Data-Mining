"use server";

import { revalidatePath } from "next/cache";

const apiBaseUrl = process.env.KDP_API_BASE_URL ?? "http://backend:8000";
const dashboardPaths = ["/", "/discovery", "/keywords", "/clusters", "/reports", "/runtime"];

function revalidateDashboardPaths() {
  for (const path of dashboardPaths) {
    revalidatePath(path);
  }
}

export async function createKeywordAction(formData: FormData) {
  const keyword = String(formData.get("keyword") ?? "").trim();
  const bookType = String(formData.get("bookType") ?? "").trim();
  const targetAudience = String(formData.get("targetAudience") ?? "").trim();
  const categoryHint = String(formData.get("categoryHint") ?? "").trim();
  const priorityRaw = String(formData.get("priority") ?? "").trim();
  const notes = String(formData.get("notes") ?? "").trim();

  if (!keyword) {
    return;
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/keywords`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      keyword,
      book_type: bookType || null,
      target_audience: targetAudience || null,
      category_hint: categoryHint || null,
      priority: priorityRaw ? Number(priorityRaw) : 0,
      notes: notes || null
    }),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to create keyword: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function expandKeywordAction(formData: FormData) {
  const keywordId = String(formData.get("keywordId") ?? "").trim();
  if (!keywordId) {
    return;
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/keywords/${keywordId}/expand-and-store`, {
    method: "POST",
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to expand keyword: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function updateKeywordAction(formData: FormData) {
  const keywordId = String(formData.get("keywordId") ?? "").trim();
  const status = String(formData.get("status") ?? "").trim();
  const priorityRaw = String(formData.get("priority") ?? "").trim();
  if (!keywordId) {
    return;
  }

  const payload: Record<string, unknown> = {};
  if (status) {
    payload.status = status;
  }
  if (priorityRaw) {
    payload.priority = Number(priorityRaw);
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/keywords/${keywordId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to update keyword: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function collectKeywordAction(formData: FormData) {
  const keywordId = String(formData.get("keywordId") ?? "").trim();
  if (!keywordId) {
    return;
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/keywords/${keywordId}/collect-search`, {
    method: "POST",
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to collect search results: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function analyzeClusterAction(formData: FormData) {
  const keywordId = String(formData.get("keywordId") ?? "").trim();
  if (!keywordId) {
    return;
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/keywords/${keywordId}/analyze-cluster`, {
    method: "POST",
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to analyze cluster: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function runPipelineAction(formData: FormData) {
  const keywordId = String(formData.get("keywordId") ?? "").trim();
  if (!keywordId) {
    return;
  }

  const response = await fetch(
    `${apiBaseUrl}/api/v1/keywords/${keywordId}/run-pipeline?collect_related_limit=8&enrich_top_books=6&review_page=1&reuse_existing_runs=true`,
    {
      method: "POST",
      cache: "no-store"
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to run pipeline: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function generateDiscoveryCandidatesAction(formData: FormData) {
  const limitRaw = String(formData.get("limit") ?? "").trim();
  const limit = limitRaw ? Number(limitRaw) : 120;

  const response = await fetch(
    `${apiBaseUrl}/api/v1/discovery/generate?limit=${encodeURIComponent(String(limit))}`,
    {
      method: "POST",
      cache: "no-store"
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to generate discovery candidates: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function runDiscoveryCycleAction(formData: FormData) {
  const generateLimitRaw = String(formData.get("generateLimit") ?? "").trim();
  const validateLimitRaw = String(formData.get("validateLimit") ?? "").trim();
  const autoGenerateReportsRaw = String(formData.get("autoGenerateReports") ?? "").trim();
  const forceRaw = String(formData.get("force") ?? "").trim();

  const generateLimit = generateLimitRaw ? Number(generateLimitRaw) : 120;
  const validateLimit = validateLimitRaw ? Number(validateLimitRaw) : 6;
  const autoGenerateReports = autoGenerateReportsRaw !== "false";
  const force = forceRaw === "true";

  const response = await fetch(
    `${apiBaseUrl}/api/v1/discovery/run-cycle?generate_limit=${encodeURIComponent(String(generateLimit))}&validate_limit=${encodeURIComponent(String(validateLimit))}&auto_generate_reports=${encodeURIComponent(String(autoGenerateReports))}&force=${encodeURIComponent(String(force))}`,
    {
      method: "POST",
      cache: "no-store"
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to run discovery cycle: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function validateDiscoveryCandidateAction(formData: FormData) {
  const candidateId = String(formData.get("candidateId") ?? "").trim();
  const autoGenerateReportsRaw = String(formData.get("autoGenerateReports") ?? "").trim();
  const forceRaw = String(formData.get("force") ?? "").trim();
  if (!candidateId) {
    return;
  }

  const autoGenerateReports = autoGenerateReportsRaw === "true";
  const force = forceRaw === "true";
  const response = await fetch(
    `${apiBaseUrl}/api/v1/discovery/candidates/${candidateId}/validate?auto_generate_reports=${encodeURIComponent(String(autoGenerateReports))}&force=${encodeURIComponent(String(force))}`,
    {
      method: "POST",
      cache: "no-store"
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to validate discovery candidate: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function generateReportAction(formData: FormData) {
  const clusterId = String(formData.get("clusterId") ?? "").trim();
  const reportType = String(formData.get("reportType") ?? "").trim();
  if (!clusterId) {
    return;
  }

  const suffix = reportType ? `?report_type=${encodeURIComponent(reportType)}` : "";
  const response = await fetch(`${apiBaseUrl}/api/v1/reports/clusters/${clusterId}/generate${suffix}`, {
    method: "POST",
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to generate report: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function analyzeSachbuchAction(formData: FormData) {
  const clusterId = String(formData.get("clusterId") ?? "").trim();
  if (!clusterId) {
    return;
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/clusters/${clusterId}/analyze-sachbuch`, {
    method: "POST",
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to analyze sachbuch cluster: ${response.status}`);
  }

  revalidateDashboardPaths();
}

export async function refreshClusterBsrAction(formData: FormData) {
  const clusterId = String(formData.get("clusterId") ?? "").trim();
  if (!clusterId) {
    return;
  }

  const response = await fetch(
    `${apiBaseUrl}/api/v1/clusters/${clusterId}/collect-bsr-snapshots?limit=5&min_hours_between_snapshots=12`,
    {
      method: "POST",
      cache: "no-store"
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to refresh BSR snapshots: ${response.status}`);
  }

  revalidateDashboardPaths();
}
