"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme-toggle";
import {
    Brain,
    Calendar,
    Users,
    Clock,
    FileText,
    CheckCircle2,
    AlertCircle,
    Download,
    Share2,
    ArrowLeft,
    RefreshCw,
    Radio,
} from "lucide-react";
import { mockMeetings } from "@/lib/mock-data";
import { format } from "date-fns";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { generateMockPDF } from "./pdf-genretor";

interface TranscriptSegment {
    speaker?: string;
    timestamp?: string;
    text: string;
}

export default function MeetingPage({ params }: { params: { id: string } }) {
    // Use the first mock meeting as default
    const meeting = mockMeetings[0];

    // Live transcript state
    const [liveTranscript, setLiveTranscript] = useState<TranscriptSegment[]>([]);
    const [isLiveMode, setIsLiveMode] = useState(false);
    const [meetingPlatform, setMeetingPlatform] = useState("google_meet");
    const [meetingId, setMeetingId] = useState("");
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [loading, setLoading] = useState(false);
    const transcriptEndRef = useRef<HTMLDivElement>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    // Auto-refresh live transcript
    useEffect(() => {
        if (isLiveMode && autoRefresh && meetingId) {
            fetchLiveTranscript();
            intervalRef.current = setInterval(() => {
                fetchLiveTranscript();
            }, 5000); // Refresh every 5 seconds

            return () => {
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
            };
        }
    }, [isLiveMode, autoRefresh, meetingId]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (transcriptEndRef.current && liveTranscript.length > 0) {
            transcriptEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [liveTranscript]);

    const fetchLiveTranscript = async () => {
        if (!meetingId) return;

        setLoading(true);
        try {
            const result = await apiClient.getTranscript(meetingPlatform, meetingId);

            if (result.transcript) {
                let segments: TranscriptSegment[] = [];

                if (Array.isArray(result.transcript)) {
                    segments = result.transcript;
                } else if (typeof result.transcript === 'string') {
                    segments = [{ text: result.transcript, timestamp: new Date().toISOString() }];
                } else if (result.transcript.segments) {
                    segments = result.transcript.segments;
                }

                setLiveTranscript(segments);
            }
        } catch (error: any) {
            console.error("Failed to fetch live transcript:", error);
            if (!error.message.includes("404")) {
                toast.error("Failed to fetch live transcript");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleEnableLiveMode = () => {
        if (!meetingId) {
            toast.error("Please enter a meeting ID");
            return;
        }
        setIsLiveMode(true);
        fetchLiveTranscript();
    };

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case "high":
                return "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20";
            case "medium":
                return "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20";
            case "low":
                return "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20";
            default:
                return "";
        }
    };

    const handleExportPDF = () => {
        try {
          const highlights = [
            "Discussed Q1 product roadmap and priority features",
            "Reviewed marketing strategy and campaign timeline",
            "Analyzed market trends and competitive landscape",
            "Evaluated budget allocation for different departments"
          ];
      
          const highPriority = [
            "Approved Q1 product roadmap with all proposed features",
            "Greenlit marketing campaign launch for January 20th",
            "Allocated additional budget for user research initiatives",
            "Scheduled follow-up meeting for January 19th"
          ];
      
          const pdfFilename = generateMockPDF({
            title: meeting.title,
            date: meeting.date,
            duration: meeting.duration,
            participants: meeting.participants.map(name => ({
              name,
              initials: name.split(" ").map(n => n[0]).join("")
            })),
      
            summary: meeting.summary,
            transcriptSummary: meeting.summary, // you can replace with real AI summary later
      
            highlights,
            highPriority,
      
            emotionAnalysis: {
              sentimentScore: meeting.emotionData.overallScore,
              engagementScore: meeting.emotionData.overallScore,
              timeline: meeting.emotionData.timeline.map(t => ({
                time: t.timestamp,
                emotion: t.emotion
              })),
              participants: meeting.participants.map(name => ({
                name,
                overallMood: "Focused",
                confidence: 80 + Math.floor(Math.random() * 10),
                engagement: 75 + Math.floor(Math.random() * 15)
              }))
            }
          });
      
          toast.success(`PDF exported successfully: ${pdfFilename}`);
        } catch (error) {
          console.error("PDF export failed:", error);
          toast.error("Failed to export PDF");
        }
      };
      

    return (
        <div className="min-h-screen bg-background">
            {/* Navigation */}
            <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-8">
                        <Link href="/" className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                                <Brain className="h-5 w-5 text-white" />
                            </div>
                            <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                                Quantum
                            </span>
                        </Link>
                        <div className="hidden md:flex items-center gap-6">
                            <Link href="/dashboard" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Dashboard
                            </Link>
                            <Link href="/meetings/1" className="text-sm font-medium text-purple-600">
                                Meetings
                            </Link>
                            <Link href="/bot-manager" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Bot Manager
                            </Link>
                            <Link href="/tasks" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Tasks
                            </Link>
                            <Link href="/calendar" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Calendar
                            </Link>
                            <Link href="/analytics/emotion" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Analytics
                            </Link>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <ThemeToggle />
                        <Avatar>
                            <AvatarFallback className="bg-gradient-to-br from-purple-500 to-blue-600 text-white">
                                SC
                            </AvatarFallback>
                        </Avatar>
                    </div>
                </div>
            </nav>

            <div className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-6">
                    <Link href="/dashboard">
                        <Button variant="ghost" className="mb-4">
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back to Dashboard
                        </Button>
                    </Link>
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <h1 className="text-3xl font-bold mb-2">{meeting.title}</h1>
                            <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                                <div className="flex items-center gap-1">
                                    <Calendar className="h-4 w-4" />
                                    {format(new Date(meeting.date), "PPP")}
                                </div>
                                <div className="flex items-center gap-1">
                                    <Clock className="h-4 w-4" />
                                    {meeting.duration} minutes
                                </div>
                                <div className="flex items-center gap-1">
                                    <Users className="h-4 w-4" />
                                    {meeting.participants.length} participants
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Button 
                                onClick={handleExportPDF}
                                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                            >
                                <Download className="h-4 w-4 mr-2" />
                                Export
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Main Content */}
                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Left Column - Transcript & Summary */}
                    <div className="lg:col-span-2 space-y-6">
                        <Card>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <CardTitle>Meeting Intelligence</CardTitle>
                                    {isLiveMode && (
                                        <Badge className="bg-green-500/10 text-green-600 border-green-500/20">
                                            <Radio className="h-3 w-3 mr-1 animate-pulse" />
                                            Live
                                        </Badge>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent>
                                <Tabs defaultValue={isLiveMode ? "transcript" : "summary"} className="w-full">
                                    <TabsList className="grid w-full grid-cols-3">
                                        <TabsTrigger value="summary">Summary</TabsTrigger>
                                        <TabsTrigger value="transcript">Transcript</TabsTrigger>
                                        <TabsTrigger value="decisions">Decisions</TabsTrigger>
                                    </TabsList>

                                    <TabsContent value="summary" className="space-y-4 mt-4">
                                        <div className="prose dark:prose-invert max-w-none">
                                            <h3 className="text-lg font-semibold mb-3">AI-Generated Summary</h3>
                                            <p className="text-muted-foreground leading-relaxed">{meeting.summary}</p>
                                        </div>
                                    </TabsContent>

                                    <TabsContent value="transcript" className="space-y-4 mt-4">
                                        {/* Live Transcript Controls */}
                                        {!isLiveMode && (
                                            <Card className="bg-muted/50 border-dashed">
                                                <CardContent className="pt-6 space-y-4">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Radio className="h-5 w-5 text-purple-600" />
                                                        <h4 className="font-semibold">Enable Live Transcript</h4>
                                                    </div>
                                                    <p className="text-sm text-muted-foreground mb-4">
                                                        Connect to an active Vexa AI bot to see real-time transcription
                                                    </p>
                                                    <div className="grid gap-3">
                                                        <div className="space-y-2">
                                                            <Label>Platform</Label>
                                                            <select
                                                                className="w-full p-2 rounded-md border bg-background"
                                                                value={meetingPlatform}
                                                                onChange={(e) => setMeetingPlatform(e.target.value)}
                                                            >
                                                                <option value="google_meet">Google Meet</option>
                                                                <option value="teams">Microsoft Teams</option>
                                                            </select>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <Label>Meeting ID</Label>
                                                            <Input
                                                                placeholder="Enter meeting ID from Bot Manager"
                                                                value={meetingId}
                                                                onChange={(e) => setMeetingId(e.target.value)}
                                                            />
                                                        </div>
                                                        <Button
                                                            onClick={handleEnableLiveMode}
                                                            className="w-full bg-gradient-to-r from-purple-600 to-blue-600"
                                                        >
                                                            <Radio className="h-4 w-4 mr-2" />
                                                            Connect to Live Transcript
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {/* Live Transcript Display */}
                                        {isLiveMode && (
                                            <div className="space-y-3">
                                                <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/50">
                                                    <div className="flex items-center gap-2">
                                                        <Badge className="bg-green-500/10 text-green-600 border-green-500/20">
                                                            <Radio className="h-3 w-3 mr-1 animate-pulse" />
                                                            Live
                                                        </Badge>
                                                        <span className="text-sm text-muted-foreground">
                                                            {meetingPlatform} - {meetingId}
                                                        </span>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() => setAutoRefresh(!autoRefresh)}
                                                        >
                                                            {autoRefresh ? "Pause" : "Resume"}
                                                        </Button>
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={fetchLiveTranscript}
                                                        >
                                                            <RefreshCw className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                </div>

                                                <div className="max-h-[500px] overflow-y-auto space-y-3 p-4 rounded-lg border bg-muted/20">
                                                    {loading && liveTranscript.length === 0 ? (
                                                        <div className="text-center py-8 text-muted-foreground">
                                                            <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin" />
                                                            <p>Loading live transcript...</p>
                                                        </div>
                                                    ) : liveTranscript.length === 0 ? (
                                                        <div className="text-center py-8 text-muted-foreground">
                                                            <p>No transcript available yet.</p>
                                                            <p className="text-sm mt-1">
                                                                Make sure the bot has joined and people are speaking.
                                                            </p>
                                                        </div>
                                                    ) : (
                                                        <>
                                                            {liveTranscript.map((segment, i) => (
                                                                <div key={i} className="flex gap-3 p-3 rounded-lg hover:bg-muted/50">
                                                                    {segment.speaker && (
                                                                        <Avatar className="h-8 w-8">
                                                                            <AvatarFallback className="text-xs">
                                                                                {segment.speaker.split(" ").map((n) => n[0]).join("")}
                                                                            </AvatarFallback>
                                                                        </Avatar>
                                                                    )}
                                                                    <div className="flex-1">
                                                                        <div className="flex items-center gap-2 mb-1">
                                                                            {segment.speaker && (
                                                                                <span className="font-medium text-sm">{segment.speaker}</span>
                                                                            )}
                                                                            {segment.timestamp && (
                                                                                <span className="text-xs text-muted-foreground">{segment.timestamp}</span>
                                                                            )}
                                                                        </div>
                                                                        <p className="text-sm text-muted-foreground">{segment.text}</p>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                            <div ref={transcriptEndRef} />
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {/* Mock Transcript (when not in live mode) */}
                                        {!isLiveMode && (
                                            <>
                                                {meeting.transcript.map((segment, i) => (
                                                    <div key={i} className="flex gap-3 p-3 rounded-lg hover:bg-muted/50">
                                                        <Avatar className="h-8 w-8">
                                                            <AvatarFallback className="text-xs">
                                                                {segment.speaker.split(" ").map((n) => n[0]).join("")}
                                                            </AvatarFallback>
                                                        </Avatar>
                                                        <div className="flex-1">
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <span className="font-medium text-sm">{segment.speaker}</span>
                                                                <span className="text-xs text-muted-foreground">{segment.timestamp}</span>
                                                            </div>
                                                            <p className="text-sm text-muted-foreground">{segment.text}</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </>
                                        )}
                                    </TabsContent>

                                    <TabsContent value="decisions" className="space-y-3 mt-4">
                                        {meeting.decisions.map((decision, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                                                <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                                                <p className="text-sm">{decision}</p>
                                            </div>
                                        ))}
                                    </TabsContent>
                                </Tabs>
                            </CardContent>
                        </Card>

                        {/* Action Items Table */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Action Items</CardTitle>
                                <CardDescription>Tasks extracted from this meeting</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Task</TableHead>
                                            <TableHead>Owner</TableHead>
                                            <TableHead>Due Date</TableHead>
                                            <TableHead>Priority</TableHead>
                                            <TableHead>Status</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {meeting.actionItems.map((item) => (
                                            <TableRow key={item.id}>
                                                <TableCell className="font-medium">{item.task}</TableCell>
                                                <TableCell>
                                                    <div className="flex items-center gap-2">
                                                        <Avatar className="h-6 w-6">
                                                            <AvatarFallback className="text-xs">
                                                                {item.owner.split(" ").map((n) => n[0]).join("")}
                                                            </AvatarFallback>
                                                        </Avatar>
                                                        <span className="text-sm">{item.owner}</span>
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-sm">{format(new Date(item.dueDate), "PP")}</TableCell>
                                                <TableCell>
                                                    <Badge variant="outline" className={getPriorityColor(item.priority)}>
                                                        {item.priority}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant="outline">
                                                        {item.status}
                                                    </Badge>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Right Column - Participants & Emotion */}
                    <div className="space-y-6">
                        {/* Participants */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Participants</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {meeting.participants.map((participant, i) => (
                                    <div key={i} className="flex items-center gap-3">
                                        <Avatar>
                                            <AvatarFallback>
                                                {participant.split(" ").map((n) => n[0]).join("")}
                                            </AvatarFallback>
                                        </Avatar>
                                        <span className="text-sm font-medium">{participant}</span>
                                    </div>
                                ))}
                            </CardContent>
                        </Card>

                        {/* Emotion Analysis */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Emotion Analysis</CardTitle>
                                <CardDescription>Overall meeting sentiment</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="text-center">
                                    <div className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                                        {meeting.emotionData.overallScore}/10
                                    </div>
                                    <p className="text-sm text-muted-foreground mt-1">Engagement Score</p>
                                </div>
                                <div className="space-y-2">
                                    <h4 className="text-sm font-medium">Emotion Timeline</h4>
                                    {meeting.emotionData.timeline.slice(0, 3).map((point, i) => (
                                        <div key={i} className="flex items-center justify-between text-sm">
                                            <span className="text-muted-foreground">{point.timestamp}</span>
                                            <Badge variant="outline" className="capitalize">
                                                {point.emotion}
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                                <Link href={`/analytics/emotion?platform=${meetingPlatform}&meetingId=${params.id}`}>
                                    <Button variant="outline" className="w-full">
                                        View Full Analysis
                                    </Button>
                                </Link>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
}