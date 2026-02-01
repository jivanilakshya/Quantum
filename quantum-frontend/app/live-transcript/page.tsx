"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ThemeToggle } from "@/components/theme-toggle";
import { Brain, RefreshCw, Download, AlertCircle, Radio, Copy, Check } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";

interface TranscriptSegment {
    speaker?: string;
    timestamp?: string;
    text: string;
    language?: string;
}

interface ActiveBot {
    platform: string;
    native_meeting_id: string;
    status: string;
}

export default function LiveTranscriptPage() {
    const [activeBots, setActiveBots] = useState<ActiveBot[]>([]);
    const [selectedBot, setSelectedBot] = useState<ActiveBot | null>(null);
    const [transcript, setTranscript] = useState<TranscriptSegment[]>([]);
    const [loading, setLoading] = useState(false);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
    const [copied, setCopied] = useState(false);
    const transcriptEndRef = useRef<HTMLDivElement>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    // Fetch active bots on mount
    useEffect(() => {
        fetchActiveBots();
    }, []);

    // Auto-refresh transcript
    useEffect(() => {
        if (autoRefresh && selectedBot) {
            fetchTranscript();
            intervalRef.current = setInterval(() => {
                fetchTranscript();
            }, 5000); // Refresh every 5 seconds

            return () => {
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
            };
        }
    }, [autoRefresh, selectedBot]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (transcriptEndRef.current) {
            transcriptEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [transcript]);

    const fetchActiveBots = async () => {
        try {
            const result = await apiClient.getBotStatus();
            if (result.bots && Array.isArray(result.bots)) {
                setActiveBots(result.bots);
                // Auto-select first bot if available
                if (result.bots.length > 0 && !selectedBot) {
                    setSelectedBot(result.bots[0]);
                }
            }
        } catch (error: any) {
            console.error("Failed to fetch active bots:", error);
        }
    };

    const fetchTranscript = async () => {
        if (!selectedBot) return;

        setLoading(true);
        try {
            const result = await apiClient.getTranscript(
                selectedBot.platform,
                selectedBot.native_meeting_id
            );

            if (result.transcript) {
                // Handle different transcript formats from Vexa API
                let segments: TranscriptSegment[] = [];

                if (Array.isArray(result.transcript)) {
                    segments = result.transcript;
                } else if (typeof result.transcript === 'string') {
                    // If transcript is a string, split into segments
                    segments = [{ text: result.transcript, timestamp: new Date().toISOString() }];
                } else if (result.transcript.segments) {
                    segments = result.transcript.segments;
                }

                setTranscript(segments);
                setLastUpdate(new Date());
            }
        } catch (error: any) {
            console.error("Failed to fetch transcript:", error);
            if (error.message.includes("404") || error.message.includes("not found")) {
                toast.error("No transcript available yet. Make sure the bot has joined the meeting.");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleBotChange = (botId: string) => {
        const bot = activeBots.find(b => `${b.platform}-${b.native_meeting_id}` === botId);
        if (bot) {
            setSelectedBot(bot);
            setTranscript([]); // Clear previous transcript
        }
    };

    const copyTranscript = () => {
        const text = transcript.map(seg => {
            const speaker = seg.speaker ? `${seg.speaker}: ` : '';
            const timestamp = seg.timestamp ? `[${seg.timestamp}] ` : '';
            return `${timestamp}${speaker}${seg.text}`;
        }).join('\n\n');

        navigator.clipboard.writeText(text);
        setCopied(true);
        toast.success("Transcript copied to clipboard!");
        setTimeout(() => setCopied(false), 2000);
    };

    const exportTranscript = () => {
        const text = transcript.map(seg => {
            const speaker = seg.speaker ? `${seg.speaker}: ` : '';
            const timestamp = seg.timestamp ? `[${seg.timestamp}] ` : '';
            return `${timestamp}${speaker}${seg.text}`;
        }).join('\n\n');

        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcript-${selectedBot?.native_meeting_id}-${new Date().toISOString()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success("Transcript exported!");
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
                            <Link href="/meetings/1" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Meetings
                            </Link>
                            <Link href="/bot-manager" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Bot Manager
                            </Link>
                            <Link href="/live-transcript" className="text-sm font-medium text-purple-600">
                                Live Transcript
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
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Live Transcript</h1>
                        <p className="text-muted-foreground">Real-time transcription from Vexa AI</p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            onClick={fetchActiveBots}
                        >
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Refresh Bots
                        </Button>
                    </div>
                </div>

                {/* Bot Selection */}
                {activeBots.length > 0 ? (
                    <Card className="mb-6">
                        <CardHeader>
                            <CardTitle>Select Active Meeting</CardTitle>
                            <CardDescription>Choose a meeting to view its live transcript</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Select
                                value={selectedBot ? `${selectedBot.platform}-${selectedBot.native_meeting_id}` : ""}
                                onValueChange={handleBotChange}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select a meeting" />
                                </SelectTrigger>
                                <SelectContent>
                                    {activeBots.map((bot) => (
                                        <SelectItem
                                            key={`${bot.platform}-${bot.native_meeting_id}`}
                                            value={`${bot.platform}-${bot.native_meeting_id}`}
                                        >
                                            {bot.platform} - {bot.native_meeting_id}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            {selectedBot && (
                                <div className="flex items-center justify-between p-4 rounded-lg border bg-muted/50">
                                    <div className="flex items-center gap-3">
                                        <Badge className="bg-green-500/10 text-green-600 border-green-500/20">
                                            <Radio className="h-3 w-3 mr-1 animate-pulse" />
                                            Live
                                        </Badge>
                                        <div>
                                            <p className="text-sm font-medium">
                                                Platform: {selectedBot.platform}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                Meeting ID: {selectedBot.native_meeting_id}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setAutoRefresh(!autoRefresh)}
                                        >
                                            {autoRefresh ? "Pause" : "Resume"} Auto-Refresh
                                        </Button>
                                        {lastUpdate && (
                                            <p className="text-xs text-muted-foreground">
                                                Last update: {lastUpdate.toLocaleTimeString()}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                ) : (
                    <Alert className="mb-6">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                            No active bots found. Please start a bot from the{" "}
                            <Link href="/bot-manager" className="font-medium underline">
                                Bot Manager
                            </Link>{" "}
                            first.
                        </AlertDescription>
                    </Alert>
                )}

                {/* Transcript Display */}
                {selectedBot && (
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>Transcript</CardTitle>
                                <CardDescription>
                                    {transcript.length > 0
                                        ? `${transcript.length} segment(s)`
                                        : "Waiting for transcript..."}
                                </CardDescription>
                            </div>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={copyTranscript}
                                    disabled={transcript.length === 0}
                                >
                                    {copied ? (
                                        <Check className="h-4 w-4 mr-2" />
                                    ) : (
                                        <Copy className="h-4 w-4 mr-2" />
                                    )}
                                    Copy
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={exportTranscript}
                                    disabled={transcript.length === 0}
                                >
                                    <Download className="h-4 w-4 mr-2" />
                                    Export
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="max-h-[600px] overflow-y-auto space-y-4 p-4 rounded-lg border bg-muted/20">
                                {loading && transcript.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin" />
                                        <p>Loading transcript...</p>
                                    </div>
                                ) : transcript.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <p>No transcript available yet.</p>
                                        <p className="text-sm mt-1">
                                            Make sure the bot has joined the meeting and people are speaking.
                                        </p>
                                    </div>
                                ) : (
                                    <>
                                        {transcript.map((segment, index) => (
                                            <div
                                                key={index}
                                                className="flex gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                                            >
                                                {segment.speaker && (
                                                    <Avatar className="h-8 w-8">
                                                        <AvatarFallback className="text-xs">
                                                            {segment.speaker
                                                                .split(" ")
                                                                .map((n) => n[0])
                                                                .join("")}
                                                        </AvatarFallback>
                                                    </Avatar>
                                                )}
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        {segment.speaker && (
                                                            <span className="font-medium text-sm">
                                                                {segment.speaker}
                                                            </span>
                                                        )}
                                                        {segment.timestamp && (
                                                            <span className="text-xs text-muted-foreground">
                                                                {segment.timestamp}
                                                            </span>
                                                        )}
                                                        {segment.language && (
                                                            <Badge variant="outline" className="text-xs">
                                                                {segment.language}
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-muted-foreground">
                                                        {segment.text}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                        <div ref={transcriptEndRef} />
                                    </>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
