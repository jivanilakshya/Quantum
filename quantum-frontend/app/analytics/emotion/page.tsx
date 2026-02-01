"use client";

import Link from "next/link";
import { useState, useEffect, Suspense } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import { ThemeToggle } from "@/components/theme-toggle";
import { Brain, Download, TrendingUp, Smile, Frown, Meh, ArrowLeft, RefreshCw, Upload, Video } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts";
import { useSearchParams } from "next/navigation";
import { Input } from "@/components/ui/input";

const emotionColors = {
    happy: "#10b981",
    neutral: "#6b7280",
    concerned: "#f59e0b",
    frustrated: "#ef4444",
};

interface EmotionTimelinePoint {
    timestamp: string;
    emotion: string;
    intensity: number;
}

function EmotionAnalyticsContent() {
    const searchParams = useSearchParams();
    const platform = searchParams?.get("platform") || "google_meet";
    const meetingId = searchParams?.get("meetingId") || "";
    
    const [engagementScore, setEngagementScore] = useState<number>(7.5);
    const [emotionTimeline, setEmotionTimeline] = useState<EmotionTimelinePoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [videoAnalysisData, setVideoAnalysisData] = useState<any>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

    useEffect(() => {
        // Check backend connection on mount
        const checkConnection = async () => {
            try {
                const connected = await apiClient.checkBackendConnection();
                setBackendConnected(connected);
                if (!connected) {
                    toast.error("Backend server is not running. Please start it with: cd quantum-backend && python main.py");
                }
            } catch (error) {
                setBackendConnected(false);
            }
        };
        checkConnection();

        if (meetingId) {
            // Check for stored summary from sessionStorage
            const storedSummary = sessionStorage.getItem(`emotion_summary_${meetingId}`);
            if (storedSummary) {
                try {
                    const summary = JSON.parse(storedSummary);
                    if (summary.success) {
                        setEngagementScore(summary.engagement_score || summary.overall_score || 7.5);
                        setEmotionTimeline(summary.timeline || []);
                        setVideoAnalysisData(summary);
                        setLoading(false);
                        // Clear stored summary after using it
                        sessionStorage.removeItem(`emotion_summary_${meetingId}`);
                        return;
                    }
                } catch (e) {
                    console.error("Failed to parse stored summary:", e);
                }
            }
            fetchEmotionData();
        } else {
            // Use default mock data if no meeting ID
            setEmotionTimeline([
                { timestamp: "00:00", emotion: "neutral", intensity: 0.7 },
                { timestamp: "00:15", emotion: "happy", intensity: 0.8 },
                { timestamp: "00:30", emotion: "concerned", intensity: 0.6 },
            ]);
            setLoading(false);
        }
    }, [meetingId, platform]);

    const fetchEmotionData = async () => {
        try {
            setLoading(true);
            const result = await apiClient.getEmotions(platform, meetingId);
            
            if (result.success) {
                setEngagementScore(result.engagement_score || result.overall_score || 7.5);
                setEmotionTimeline(result.timeline || []);
            }
        } catch (error: any) {
            console.error("Failed to fetch emotion data:", error);
            toast.error("Failed to load emotion analysis. Using default data.");
            // Use default data on error
            setEmotionTimeline([
                { timestamp: "00:00", emotion: "neutral", intensity: 0.7 },
                { timestamp: "00:15", emotion: "happy", intensity: 0.8 },
                { timestamp: "00:30", emotion: "concerned", intensity: 0.6 },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleVideoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('video/')) {
            toast.error("Please select a video file");
            return;
        }

        // Check file size (limit to 500MB)
        const maxSize = 500 * 1024 * 1024; // 500MB
        if (file.size > maxSize) {
            toast.error("Video file is too large. Maximum size is 500MB.");
            return;
        }

        setSelectedFile(file);
        setUploading(true);

        try {
            console.log("Uploading video file:", file.name, "Size:", (file.size / 1024 / 1024).toFixed(2), "MB");
            console.log("API Base URL:", process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');
            
            const result = await apiClient.analyzeVideoEmotions(file, meetingId || undefined);
            
            if (result.success) {
                setVideoAnalysisData(result);
                setEngagementScore(result.engagement_score || result.overall_score || 7.5);
                setEmotionTimeline(result.timeline || []);
                toast.success("Video analysis completed successfully!");
            } else {
                toast.error(result.message || "Video analysis failed");
            }
        } catch (error: any) {
            console.error("Failed to analyze video:", error);
            const errorMessage = error.message || "Failed to analyze video. Please check if the backend server is running.";
            
            // Show detailed error in toast
            toast.error(errorMessage, {
                duration: 10000, // Show for 10 seconds
            });
            
            // Also log to console for debugging
            console.error("Full error details:", {
                message: error.message,
                stack: error.stack,
                name: error.name,
            });
        } finally {
            setUploading(false);
        }
    };

    const getEmotionBadgeColor = (emotion: string) => {
        switch (emotion.toLowerCase()) {
            case "happy":
                return "bg-green-500/10 text-green-600 border-green-500/20 hover:bg-green-500/20";
            case "neutral":
                return "bg-gray-500/10 text-gray-600 border-gray-500/20 hover:bg-gray-500/20";
            case "concerned":
                return "bg-orange-500/10 text-orange-600 border-orange-500/20 hover:bg-orange-500/20";
            case "frustrated":
                return "bg-red-500/10 text-red-600 border-red-500/20 hover:bg-red-500/20";
            case "sad":
                return "bg-blue-500/10 text-blue-600 border-blue-500/20 hover:bg-blue-500/20";
            case "angry":
                return "bg-red-500/10 text-red-600 border-red-500/20 hover:bg-red-500/20";
            case "surprise":
                return "bg-yellow-500/10 text-yellow-600 border-yellow-500/20 hover:bg-yellow-500/20";
            case "fear":
                return "bg-purple-500/10 text-purple-600 border-purple-500/20 hover:bg-purple-500/20";
            default:
                return "bg-gray-500/10 text-gray-600 border-gray-500/20";
        }
    };

    // Prepare data for charts
    const emotionDistribution = videoAnalysisData?.summary?.overall_emotion_distribution
        ? (() => {
            const distribution = videoAnalysisData.summary.overall_emotion_distribution as Record<string, number>;
            const total = Object.values(distribution).reduce((a, b) => a + b, 0);
            return Object.entries(distribution).map(([emotion, count]) => {
                const percentage = total > 0 ? (count / total) * 100 : 0;
                return {
                    name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
                    value: Math.round(percentage),
                    color: emotionColors[emotion.toLowerCase() as keyof typeof emotionColors] || emotionColors.neutral
                };
            });
        })()
        : [
            { name: "Happy", value: 65, color: emotionColors.happy },
            { name: "Neutral", value: 25, color: emotionColors.neutral },
            { name: "Concerned", value: 8, color: emotionColors.concerned },
            { name: "Frustrated", value: 2, color: emotionColors.frustrated },
        ];

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
                            <Link href="/tasks" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Tasks
                            </Link>
                            <Link href="/calendar" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                                Calendar
                            </Link>
                            <Link href="/analytics/emotion" className="text-sm font-medium text-purple-600">
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

            <div className="container mx-auto px-4 py-8 max-w-4xl">
                {/* Back Button */}
                <div className="flex items-center justify-between mb-6">
                    <Link href={meetingId ? `/meetings/${meetingId}` : "/dashboard"}>
                        <Button variant="ghost">
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back
                        </Button>
                    </Link>
                    
                    {/* Video Upload Button */}
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Input
                                type="file"
                                accept="video/*"
                                onChange={handleVideoUpload}
                                className="hidden"
                                id="video-upload"
                                disabled={uploading || backendConnected === false}
                            />
                            <Button
                                variant="outline"
                                onClick={() => document.getElementById('video-upload')?.click()}
                                disabled={uploading || backendConnected === false}
                                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0 disabled:opacity-50"
                            >
                                {uploading ? (
                                    <>
                                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                        Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <Upload className="h-4 w-4 mr-2" />
                                        Analyze Video
                                    </>
                                )}
                            </Button>
                        </div>
                        {selectedFile && (
                            <span className="text-sm text-muted-foreground">
                                {selectedFile.name}
                            </span>
                        )}
                        {backendConnected === false && (
                            <Badge variant="destructive" className="ml-2">
                                Backend Offline
                            </Badge>
                        )}
                        {backendConnected === true && (
                            <Badge variant="outline" className="ml-2 bg-green-500/10 text-green-600 border-green-500/20">
                                Backend Connected
                            </Badge>
                        )}
                    </div>
                </div>

                {/* Meeting Mood Summary - Prominent Display */}
                {videoAnalysisData?.summary && (
                    <Card className="border-2 mb-6 bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20">
                        <CardHeader>
                            <CardTitle className="text-2xl flex items-center gap-2">
                                <Brain className="h-6 w-6 text-purple-600" />
                                Overall Meeting Mood Summary
                            </CardTitle>
                            <CardDescription>
                                Complete emotion analysis from your meeting
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                                <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
                                    <div className="text-4xl font-bold text-purple-600 mb-2">
                                        {engagementScore.toFixed(1)}/10
                                    </div>
                                    <div className="text-sm text-muted-foreground">Engagement Score</div>
                                    <Progress value={engagementScore * 10} className="mt-2" />
                                </div>
                                <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
                                    <div className="text-4xl font-bold text-blue-600 mb-2">
                                        {videoAnalysisData.summary.total_people_active || 0}
                                    </div>
                                    <div className="text-sm text-muted-foreground">Participants Analyzed</div>
                                </div>
                                <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
                                    <div className="text-4xl font-bold text-green-600 mb-2">
                                        {Math.round(videoAnalysisData.summary.meeting_duration || 0)}s
                                    </div>
                                    <div className="text-sm text-muted-foreground">Meeting Duration</div>
                                </div>
                            </div>
                            
                            {videoAnalysisData.summary.overall_emotion_distribution && (
                                <div className="mt-4">
                                    <h4 className="font-semibold mb-3">Emotion Distribution</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {Object.entries(videoAnalysisData.summary.overall_emotion_distribution).map(([emotion, count]: [string, any]) => {
                                            const distribution = videoAnalysisData.summary.overall_emotion_distribution as Record<string, number>;
                                            const total = Object.values(distribution).reduce((a, b) => a + b, 0);
                                            const percentage = total > 0 ? ((count as number) / total) * 100 : 0;
                                            return (
                                                <Badge
                                                    key={emotion}
                                                    variant="outline"
                                                    className={`px-4 py-2 rounded-full text-sm font-medium ${getEmotionBadgeColor(emotion)}`}
                                                >
                                                    {emotion.charAt(0).toUpperCase() + emotion.slice(1)}: {percentage.toFixed(1)}%
                                                </Badge>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Emotion Analysis Card - Matching Image Design */}
                <Card className="border-2">
                    <CardHeader>
                        <CardTitle className="text-2xl">Emotion Analysis</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-8">
                        {loading ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin" />
                                <p>Loading emotion analysis...</p>
                            </div>
                        ) : (
                            <>
                                {/* Overall Meeting Sentiment Section */}
                                <div className="space-y-2">
                                    <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                                        Overall meeting sentiment
                                    </h3>
                                    <div className="text-6xl font-bold bg-gradient-to-r from-purple-600 to-purple-800 bg-clip-text text-transparent">
                                        {engagementScore.toFixed(1)}/10
                                    </div>
                                    <p className="text-sm font-medium text-muted-foreground">Engagement Score</p>
                                </div>

                                {/* Emotion Timeline Section */}
                                <div className="space-y-4">
                                    <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                                        Emotion Timeline
                                    </h3>
                                    <div className="flex flex-wrap gap-3">
                                        {emotionTimeline.length > 0 ? (
                                            emotionTimeline.map((point, index) => (
                                                <div key={index} className="flex items-center gap-2">
                                                    <span className="text-xs text-muted-foreground font-mono">{point.timestamp}</span>
                                                    <Badge
                                                        variant="outline"
                                                        className={`px-4 py-2 rounded-full text-sm font-medium capitalize ${getEmotionBadgeColor(point.emotion)}`}
                                                    >
                                                        {point.emotion}
                                                    </Badge>
                                                </div>
                                            ))
                                        ) : (
                                            <>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-muted-foreground font-mono">00:00</span>
                                                    <Badge variant="outline" className="px-4 py-2 rounded-full text-sm font-medium bg-gray-500/10 text-gray-600 border-gray-500/20">
                                                        Neutral
                                                    </Badge>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-muted-foreground font-mono">00:15</span>
                                                    <Badge variant="outline" className="px-4 py-2 rounded-full text-sm font-medium bg-green-500/10 text-green-600 border-green-500/20">
                                                        Happy
                                                    </Badge>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-muted-foreground font-mono">00:30</span>
                                                    <Badge variant="outline" className="px-4 py-2 rounded-full text-sm font-medium bg-orange-500/10 text-orange-600 border-orange-500/20">
                                                        Concerned
                                                    </Badge>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </div>

                                {/* View Full Analysis Button */}
                                <div className="pt-4 border-t">
                                    <Button 
                                        variant="outline" 
                                        className="w-full bg-muted hover:bg-muted/80 text-foreground"
                                        onClick={() => {
                                            // Scroll to detailed view below or navigate to detailed page
                                            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                                        }}
                                    >
                                        View Full Analysis
                                    </Button>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>

                {/* Detailed Analytics Section (shown after clicking "View Full Analysis") */}
                {!loading && (
                    <div className="mt-8 space-y-6">
                        {/* Overview Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
                                    <Smile className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{engagementScore.toFixed(1)}/10</div>
                                    <Progress value={engagementScore * 10} className="mt-2" />
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Positive Moments</CardTitle>
                                    <TrendingUp className="h-4 w-4 text-green-600" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">
                                        {Math.round((emotionTimeline.filter(e => e.emotion === 'happy').length / Math.max(emotionTimeline.length, 1)) * 100)}%
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">Of meeting duration</p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Engagement Level</CardTitle>
                                    <Smile className="h-4 w-4 text-blue-600" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">
                                        {engagementScore >= 8 ? 'High' : engagementScore >= 6 ? 'Medium' : 'Low'}
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">Above average</p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Concerns Detected</CardTitle>
                                    <Frown className="h-4 w-4 text-orange-600" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">
                                        {emotionTimeline.filter(e => e.emotion === 'concerned' || e.emotion === 'frustrated').length}
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">Requires attention</p>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Video Analysis Summary */}
                        {videoAnalysisData?.summary && (
                            <Card className="mb-6">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Video className="h-5 w-5" />
                                        Video Analysis Summary
                                    </CardTitle>
                                    <CardDescription>
                                        Analysis results from uploaded video
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div>
                                            <div className="text-sm text-muted-foreground">Duration</div>
                                            <div className="text-lg font-semibold">
                                                {Math.round(videoAnalysisData.summary.meeting_duration)}s
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-sm text-muted-foreground">People Detected</div>
                                            <div className="text-lg font-semibold">
                                                {videoAnalysisData.summary.total_people_active}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-sm text-muted-foreground">Total Detected</div>
                                            <div className="text-lg font-semibold">
                                                {videoAnalysisData.summary.total_people_detected}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-sm text-muted-foreground">Analysis Method</div>
                                            <div className="text-lg font-semibold">Video AI</div>
                                        </div>
                                    </div>
                                    
                                    {videoAnalysisData.summary.people && videoAnalysisData.summary.people.length > 0 && (
                                        <div className="mt-6 space-y-4">
                                            <h4 className="font-semibold">Per-Person Analysis</h4>
                                            {videoAnalysisData.summary.people.map((person: any, idx: number) => (
                                                <Card key={idx} className="p-4">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className="font-medium">{person.person_name}</div>
                                                        <Badge variant="outline" className={getEmotionBadgeColor(person.dominant_emotion || 'neutral')}>
                                                            {person.dominant_emotion || 'N/A'}
                                                        </Badge>
                                                    </div>
                                                    <div className="text-sm text-muted-foreground mb-2">
                                                        Speaking: {person.speaking_percentage?.toFixed(1)}%
                                                    </div>
                                                    {person.emotion_percentages && (
                                                        <div className="flex flex-wrap gap-2">
                                                            {Object.entries(person.emotion_percentages).map(([emotion, pct]: [string, any]) => (
                                                                <Badge key={emotion} variant="outline" className="text-xs">
                                                                    {emotion}: {pct.toFixed(1)}%
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    )}
                                                </Card>
                                            ))}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        )}

                        {/* Charts Section */}
                        <div className="grid lg:grid-cols-2 gap-6">
                            {/* Emotion Timeline Chart */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>Emotion Timeline</CardTitle>
                                    <CardDescription>How emotions evolved throughout the meeting</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {emotionTimeline.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={300}>
                                            <LineChart data={emotionTimeline}>
                                                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                                <XAxis dataKey="timestamp" className="text-xs" />
                                                <YAxis domain={[0, 1]} className="text-xs" />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: "hsl(var(--background))",
                                                        border: "1px solid hsl(var(--border))",
                                                    }}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="intensity"
                                                    stroke="#9333ea"
                                                    strokeWidth={3}
                                                    dot={{ fill: "#9333ea", r: 4 }}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                                            No timeline data available
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* Emotion Distribution */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>Emotion Distribution</CardTitle>
                                    <CardDescription>Overall sentiment breakdown</CardDescription>
                                </CardHeader>
                                <CardContent className="flex items-center justify-center">
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie
                                                data={emotionDistribution}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ name, value }) => `${name}: ${value}%`}
                                                outerRadius={100}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {emotionDistribution.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function EmotionAnalyticsPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-muted-foreground" />
                    <p className="text-muted-foreground">Loading...</p>
                </div>
            </div>
        }>
            <EmotionAnalyticsContent />
        </Suspense>
    );
}
