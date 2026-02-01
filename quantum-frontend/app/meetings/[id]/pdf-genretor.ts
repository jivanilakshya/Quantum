import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

interface MockMeeting {
  title: string;
  date: string;
  duration: number;
  participants: Array<{ name: string; initials: string }>;

  summary: string;
  transcriptSummary?: string;

  highlights?: string[];
  highPriority?: string[];

  emotionAnalysis?: {
    sentimentScore: number;
    engagementScore: number;
    timeline: Array<{ time: string; emotion: string }>;
    participants: Array<{
      name: string;
      overallMood: string;
      confidence: number;
      engagement: number;
    }>;
  };
}

export const generateMockPDF = (meeting: MockMeeting) => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  let yPosition = 60;

  // Corporate theme
const primary = "rgb(32,64,145)";
const accent = "rgb(99,102,241)";
const textDark = "rgb(33,33,33)";
const textGray = "rgb(110,110,110)";


  // Header
  doc.setFillColor(primary.toString());
  doc.rect(0, 0, pageWidth, 50, "F");

  doc.setTextColor(textDark.toString());
  doc.setFontSize(24);
  doc.setFont("helvetica", "bold");
  doc.text("Corporate Meeting Report", 20, 30);

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text("Confidential Business Document", 20, 42);

  // Meta Info
  doc.setTextColor(accent.toString());
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text(meeting.title, 20, yPosition);

  yPosition += 10;
  doc.setFontSize(9.5);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(textGray.toString());

  doc.text(`Date: ${new Date(meeting.date).toDateString()}`, 20, yPosition);
  yPosition += 6;
  doc.text(`Duration: ${meeting.duration} minutes`, 20, yPosition);
  yPosition += 6;
  doc.text(`Participants: ${meeting.participants.length}`, 20, yPosition);

  yPosition += 15;

  const drawSectionTitle = (title: string) => {
    doc.setDrawColor(accent.toString());
    doc.setLineWidth(0.5);
    doc.line(20, yPosition - 3, pageWidth - 20, yPosition - 3);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.setTextColor(primary.toString());
    doc.text(title, 20, yPosition);

    yPosition += 8;
  };

  // Executive Summary
  drawSectionTitle("Executive Summary");

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10.5);
  doc.setTextColor(textDark.toString());

  const summaryLines = doc.splitTextToSize(meeting.summary, pageWidth - 40);
  doc.text(summaryLines, 20, yPosition);
  yPosition += summaryLines.length * 6 + 10;

  // Meeting Intelligence
  drawSectionTitle("Meeting Intelligence");

  if (meeting.transcriptSummary) {
    doc.setFont("helvetica", "bold");
    doc.text("Transcript Summary", 20, yPosition);
    yPosition += 6;

    doc.setFont("helvetica", "normal");
    const tLines = doc.splitTextToSize(meeting.transcriptSummary, pageWidth - 40);
    doc.text(tLines, 25, yPosition);
    yPosition += tLines.length * 6 + 6;
  }

  if (meeting.highlights?.length) {
    doc.setFont("helvetica", "bold");
    doc.text("Key Highlights", 20, yPosition);
    yPosition += 6;

    doc.setFont("helvetica", "normal");
    meeting.highlights.forEach(h => {
      doc.text(`• ${h}`, 25, yPosition);
      yPosition += 6;
    });
    yPosition += 4;
  }

  if (meeting.highPriority?.length) {
    doc.setFont("helvetica", "bold");
    doc.text("High Priority Focus", 20, yPosition);
    yPosition += 6;

    doc.setFont("helvetica", "normal");
    meeting.highPriority.forEach(p => {
      doc.text(`★ ${p}`, 25, yPosition);
      yPosition += 6;
    });
    yPosition += 10;
  }

  // Emotion Analysis
  if (meeting.emotionAnalysis) {
    drawSectionTitle("Behavioral & Engagement Analysis");

    const { sentimentScore, engagementScore, timeline, participants } = meeting.emotionAnalysis;

    doc.setFont("helvetica", "normal");
    doc.setTextColor(textDark.toString());

    doc.text(`Overall Sentiment Index: ${sentimentScore}/10`, 20, yPosition);
    yPosition += 6;
    doc.text(`Engagement Index: ${engagementScore}/10`, 20, yPosition);
    yPosition += 10;

    doc.setFont("helvetica", "bold");
    doc.text("Emotion Timeline", 20, yPosition);
    yPosition += 6;

    doc.setFont("helvetica", "normal");
    timeline.forEach(e => {
      doc.text(`${e.time} — ${e.emotion}`, 25, yPosition);
      yPosition += 5;
    });

    yPosition += 8;

    autoTable(doc, {
      startY: yPosition,
      head: [["Participant", "Overall Mood", "Confidence", "Engagement"]],
      body: participants.map(p => [
        p.name,
        p.overallMood,
        `${p.confidence}%`,
        `${p.engagement}%`
      ]),
      theme: "grid",
      headStyles: { fillColor: primary.toString(), textColor: 255, fontSize: 10, halign: "center" },
      bodyStyles: { fontSize: 9.5, textColor: textDark.toString() },
      alternateRowStyles: { fillColor: [245, 247, 252] },
      styles: { lineColor: [220, 220, 220] }
    });

    yPosition = (doc as any).lastAutoTable.finalY + 10;
  }

  // Footer
  const pageCount = (doc as any).internal.getNumberOfPages();
  doc.setFontSize(8);
  doc.setTextColor(textGray.toString());

  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.text(
      `Prepared by Briefly Intelligence Suite • ${new Date().toLocaleDateString()} • Page ${i} of ${pageCount}`,
      pageWidth / 2,
      pageHeight - 10,
      { align: "center" }
    );
  }

  doc.save(`${meeting.title.replace(/\s+/g, "_")}.pdf`);
};
