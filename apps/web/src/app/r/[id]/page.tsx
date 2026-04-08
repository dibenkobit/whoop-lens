import { notFound } from "next/navigation";

import { getSharedReport } from "@/lib/api";

import { SharedReportView } from "./SharedReportView";

export const dynamic = "force-dynamic";

type Params = { id: string };

export default async function Page({ params }: { params: Promise<Params> }) {
  const { id } = await params;
  const report = await getSharedReport(id);
  if (!report) notFound();
  return <SharedReportView report={report} />;
}
