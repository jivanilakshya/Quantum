// Mock data for Quantum platform demo

export interface Meeting {
    id: string;
    title: string;
    date: string;
    duration: number;
    participants: string[];
    transcript: TranscriptSegment[];
    summary: string;
    decisions: string[];
    actionItems: ActionItem[];
    emotionData: EmotionData;
}

export interface TranscriptSegment {
    speaker: string;
    timestamp: string;
    text: string;
}

export interface ActionItem {
    id: string;
    task: string;
    owner: string;
    dueDate: string;
    priority: "high" | "medium" | "low";
    status: "todo" | "in-progress" | "done";
    meetingId: string;
}

export interface EmotionData {
    timeline: EmotionTimelinePoint[];
    overallScore: number;
    speakerEmotions: Record<string, EmotionBreakdown>;
}

export interface EmotionTimelinePoint {
    timestamp: string;
    emotion: string;
    intensity: number;
}

export interface EmotionBreakdown {
    happy: number;
    neutral: number;
    concerned: number;
    frustrated: number;
}

export const mockMeetings: Meeting[] = [
    {
        id: "1",
        title: "Q1 Product Planning",
        date: "2026-01-05T10:00:00Z",
        duration: 45,
        participants: ["Sarah Chen", "Mike Johnson", "Priya Patel", "Alex Kumar"],
        transcript: [
            {
                speaker: "Sarah Chen",
                timestamp: "00:00",
                text: "Good morning everyone. Let's discuss our Q1 product roadmap. We need to prioritize the AI features.",
            },
            {
                speaker: "Mike Johnson",
                timestamp: "00:15",
                text: "I agree. The emotion analysis module is getting great feedback from beta users.",
            },
            {
                speaker: "Priya Patel",
                timestamp: "00:30",
                text: "We should also focus on the Jira integration. Many enterprise clients are requesting it.",
            },
            {
                speaker: "Alex Kumar",
                timestamp: "00:45",
                text: "I can lead the integration work. We'll need about 2 weeks for the initial implementation.",
            },
        ],
        summary:
            "The team discussed Q1 product priorities, focusing on AI features and enterprise integrations. Key decisions were made regarding the emotion analysis module and Jira integration timeline.",
        decisions: [
            "Prioritize emotion analysis module for Q1 release",
            "Allocate 2 weeks for Jira integration development",
            "Schedule weekly check-ins for progress tracking",
        ],
        actionItems: [
            {
                id: "a1",
                task: "Complete Jira integration API design",
                owner: "Alex Kumar",
                dueDate: "2026-01-12",
                priority: "high",
                status: "in-progress",
                meetingId: "1",
            },
            {
                id: "a2",
                task: "Prepare emotion analysis demo for stakeholders",
                owner: "Mike Johnson",
                dueDate: "2026-01-10",
                priority: "high",
                status: "todo",
                meetingId: "1",
            },
            {
                id: "a3",
                task: "Document API requirements for enterprise clients",
                owner: "Priya Patel",
                dueDate: "2026-01-15",
                priority: "medium",
                status: "todo",
                meetingId: "1",
            },
        ],
        emotionData: {
            timeline: [
                { timestamp: "00:00", emotion: "neutral", intensity: 0.7 },
                { timestamp: "00:15", emotion: "happy", intensity: 0.8 },
                { timestamp: "00:30", emotion: "concerned", intensity: 0.6 },
                { timestamp: "00:45", emotion: "happy", intensity: 0.9 },
            ],
            overallScore: 7.5,
            speakerEmotions: {
                "Sarah Chen": { happy: 60, neutral: 30, concerned: 10, frustrated: 0 },
                "Mike Johnson": { happy: 70, neutral: 25, concerned: 5, frustrated: 0 },
                "Priya Patel": { happy: 50, neutral: 35, concerned: 15, frustrated: 0 },
                "Alex Kumar": { happy: 80, neutral: 15, concerned: 5, frustrated: 0 },
            },
        },
    },
    {
        id: "2",
        title: "Sprint Retrospective",
        date: "2026-01-03T14:00:00Z",
        duration: 30,
        participants: ["Sarah Chen", "Dev Team"],
        transcript: [
            {
                speaker: "Sarah Chen",
                timestamp: "00:00",
                text: "Let's review what went well and what we can improve from the last sprint.",
            },
        ],
        summary:
            "Team reflected on sprint performance, identified blockers, and planned improvements for next sprint.",
        decisions: [
            "Implement daily standups at 9 AM",
            "Use automated testing for all new features",
        ],
        actionItems: [
            {
                id: "a4",
                task: "Set up automated testing pipeline",
                owner: "Dev Team",
                dueDate: "2026-01-08",
                priority: "high",
                status: "todo",
                meetingId: "2",
            },
        ],
        emotionData: {
            timeline: [
                { timestamp: "00:00", emotion: "neutral", intensity: 0.6 },
                { timestamp: "00:15", emotion: "happy", intensity: 0.7 },
            ],
            overallScore: 6.8,
            speakerEmotions: {
                "Sarah Chen": { happy: 55, neutral: 40, concerned: 5, frustrated: 0 },
            },
        },
    },
];

export const dashboardStats = {
    totalMeetings: 24,
    tasksCreated: 87,
    followUpsScheduled: 12,
    avgEmotionScore: 7.2,
};

export const recentActivity = [
    {
        id: "1",
        type: "meeting",
        title: "Q1 Product Planning completed",
        timestamp: "2 hours ago",
    },
    {
        id: "2",
        type: "task",
        title: "New task assigned: Complete Jira integration",
        timestamp: "3 hours ago",
    },
    {
        id: "3",
        type: "followup",
        title: "Follow-up scheduled for Sprint Planning",
        timestamp: "1 day ago",
    },
];
