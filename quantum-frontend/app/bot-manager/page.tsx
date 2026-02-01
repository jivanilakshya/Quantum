"use client";

import Link from "next/link";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/theme-toggle";
import { Brain, Play, Square, RefreshCw, AlertCircle, CheckCircle2, Loader2, Radio } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";

interface ActiveBot {
    platform: string;
    meeting_id: string;
    status: string;
}

export default function BotManagementPage() {
    const [platform, setPlatform] = useState<string>("google_meet");
    const [meetingUrl, setMeetingUrl] = useState<string>("");
    const [language, setLanguage] = useState<string>("en");
    const [botName, setBotName] = useState<string>("Quantum AI Bot");
    const [loading, setLoading] = useState<boolean>(false);
    const [activeBots, setActiveBots] = useState<ActiveBot[]>([]);
    const [currentMeetingId, setCurrentMeetingId] = useState<string>("");

    const handleStartBot = async () => {
        if (!meetingUrl) {
            toast.error("Please enter a meeting URL");
            return;
        }

        setLoading(true);
        try {
            const result = await apiClient.startBot(platform, meetingUrl, language, botName);
            toast.success(result.message || "Bot started successfully!");
            setCurrentMeetingId(result.meeting_id);

            // Start emotion analysis in parallel
            try {
                await apiClient.startEmotionAnalysis(platform, result.meeting_id);
                toast.success("Emotion analysis started!");
            } catch (emotionError: any) {
                console.error("Failed to start emotion analysis:", emotionError);
                // Don't fail the whole operation if emotion analysis fails
                toast.warning("Bot started, but emotion analysis failed to start");
            }

            // Refresh bot status
            setTimeout(() => {
                refreshBotStatus();
            }, 2000);
        } catch (error: any) {
            toast.error(error.message || "Failed to start bot");
        } finally {
            setLoading(false);
        }
    };

    const handleStopBot = async (botPlatform: string, meetingId: string) => {
        setLoading(true);
        try {
            // Stop emotion analysis first and get summary
            let emotionSummary = null;
            try {
                emotionSummary = await apiClient.stopEmotionAnalysis(botPlatform, meetingId);
                if (emotionSummary.success) {
                    // Store summary for display
                    sessionStorage.setItem(`emotion_summary_${meetingId}`, JSON.stringify(emotionSummary));
                    toast.success(`Meeting mood: ${emotionSummary.engagement_score}/10 engagement score`);
                }
            } catch (emotionError: any) {
                console.error("Failed to stop emotion analysis:", emotionError);
                // Continue even if emotion analysis fails
            }

            const result = await apiClient.stopBot(botPlatform, meetingId);
            toast.success(result.message || "Bot stopped successfully! API credits freed.");
            setCurrentMeetingId("");

            // Navigate to emotion analytics if summary available
            if (emotionSummary?.success) {
                setTimeout(() => {
                    window.location.href = `/analytics/emotion?platform=${botPlatform}&meetingId=${meetingId}`;
                }, 1500);
            } else {
                // Refresh bot status
                setTimeout(() => {
                    refreshBotStatus();
                }, 1000);
            }
        } catch (error: any) {
            toast.error(error.message || "Failed to stop bot");
        } finally {
            setLoading(false);
        }
    };

    const refreshBotStatus = async () => {
        try {
            const result = await apiClient.getBotStatus();
            if (result.bots && Array.isArray(result.bots)) {
                setActiveBots(result.bots);
            }
        } catch (error: any) {
            console.error("Failed to get bot status:", error);
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
                            <Link href="/meetings/1" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Meetings
                            </Link>
                            <Link href="/bot-manager" className="text-sm font-medium text-purple-600">
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
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Meeting Bot Manager</h1>
                    <p className="text-muted-foreground">
                        Start a Vexa AI bot to transcribe your meetings in real-time
                    </p>
                </div>

                {/* Important Notice */}
                <Alert className="mb-6 border-orange-500/20 bg-orange-500/10">
                    <AlertCircle className="h-4 w-4 text-orange-600" />
                    <AlertDescription className="text-orange-600 dark:text-orange-400">
                        <strong>Important:</strong> Always click "End Call" when your meeting is finished to free up API credits!
                    </AlertDescription>
                </Alert>

                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Start Bot Form */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Start New Bot</CardTitle>
                            <CardDescription>Add a transcription bot to your meeting</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="platform">Meeting Platform</Label>
                                <Select value={platform} onValueChange={setPlatform}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="google_meet">Google Meet</SelectItem>
                                        <SelectItem value="teams">Microsoft Teams</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="meetingUrl">Meeting URL</Label>
                                <Input
                                    id="meetingUrl"
                                    placeholder={
                                        platform === "google_meet"
                                            ? "https://meet.google.com/abc-defg-hij"
                                            : "https://teams.live.com/meet/1234567890?p=xxx"
                                    }
                                    value={meetingUrl}
                                    onChange={(e) => setMeetingUrl(e.target.value)}
                                />
                                <p className="text-xs text-muted-foreground">
                                    {platform === "google_meet"
                                        ? "Paste the full Google Meet URL"
                                        : "Paste the full Microsoft Teams URL (must include passcode)"}
                                </p>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="language">Language</Label>
                                <Select value={language} onValueChange={setLanguage}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="en">English</SelectItem>
                                        <SelectItem value="hi">Hindi</SelectItem>
                                        <SelectItem value="gu">Gujarati</SelectItem>
                                        <SelectItem value="es">Spanish</SelectItem>
                                        <SelectItem value="fr">French</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="botName">Bot Name (Optional)</Label>
                                <Input
                                    id="botName"
                                    placeholder="Quantum AI Bot"
                                    value={botName}
                                    onChange={(e) => setBotName(e.target.value)}
                                />
                            </div>

                            <Button
                                onClick={handleStartBot}
                                disabled={loading || !meetingUrl}
                                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Starting Bot...
                                    </>
                                ) : (
                                    <>
                                        <Play className="h-4 w-4 mr-2" />
                                        Start Bot
                                    </>
                                )}
                            </Button>

                            <p className="text-xs text-muted-foreground text-center">
                                The bot will request to join the meeting in ~10 seconds
                            </p>
                        </CardContent>
                    </Card>

                    {/* Active Bots */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>Active Bots</CardTitle>
                                <CardDescription>Currently running transcription bots</CardDescription>
                            </div>
                            <Button variant="outline" size="icon" onClick={refreshBotStatus}>
                                <RefreshCw className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {currentMeetingId && (
                                <div className="p-4 rounded-lg border bg-purple-500/5 border-purple-500/20">
                                    <div className="flex items-start justify-between mb-3">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <Badge className="bg-green-500/10 text-green-600 border-green-500/20">
                                                    <CheckCircle2 className="h-3 w-3 mr-1" />
                                                    Active
                                                </Badge>
                                                <Badge variant="outline">{platform}</Badge>
                                            </div>
                                            <p className="text-sm font-medium mt-2">Meeting ID: {currentMeetingId}</p>
                                            <p className="text-xs text-muted-foreground">Language: {language.toUpperCase()}</p>
                                        </div>
                                    </div>


                                    <div className="space-y-2">
                                        <Link href="/live-transcript">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="w-full"
                                            >
                                                <Radio className="h-4 w-4 mr-2" />
                                                View Live Transcript
                                            </Button>
                                        </Link>
                                        <Button
                                            variant="destructive"
                                            size="sm"
                                            onClick={() => handleStopBot(platform, currentMeetingId)}
                                            disabled={loading}
                                            className="w-full"
                                        >
                                            {loading ? (
                                                <>
                                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                    Stopping...
                                                </>
                                            ) : (
                                                <>
                                                    <Square className="h-4 w-4 mr-2" />
                                                    End Call & Free Credits
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {!currentMeetingId && activeBots.length === 0 && (
                                <div className="text-center py-8 text-muted-foreground">
                                    <p>No active bots</p>
                                    <p className="text-sm mt-1">Start a bot to begin transcription</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Instructions */}
                <Card className="mt-6">
                    <CardHeader>
                        <CardTitle>How to Use</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid md:grid-cols-3 gap-4">
                            <div className="space-y-2">
                                <div className="h-10 w-10 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-600 font-bold">
                                    1
                                </div>
                                <h4 className="font-medium">Create Meeting</h4>
                                <p className="text-sm text-muted-foreground">
                                    Start a Google Meet or Microsoft Teams meeting and copy the URL
                                </p>
                            </div>
                            <div className="space-y-2">
                                <div className="h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-600 font-bold">
                                    2
                                </div>
                                <h4 className="font-medium">Start Bot</h4>
                                <p className="text-sm text-muted-foreground">
                                    Paste the URL, select language, and click "Start Bot". Admit the bot when it requests to join.
                                </p>
                            </div>
                            <div className="space-y-2">
                                <div className="h-10 w-10 rounded-full bg-green-500/10 flex items-center justify-center text-green-600 font-bold">
                                    3
                                </div>
                                <h4 className="font-medium">End Call</h4>
                                <p className="text-sm text-muted-foreground">
                                    When finished, click "End Call" to stop the bot and free up your API credits
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
