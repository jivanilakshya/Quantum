"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/theme-toggle";
import { Brain, Video, Plus, Clock, Users, ChevronLeft, ChevronRight, Calendar as CalendarIcon, FileText, ArrowRight, CheckSquare } from "lucide-react";
import { mockMeetings, Meeting } from "@/lib/mock-data";
import { format } from "date-fns";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

interface Task {
    id: string;
    title: string;
    description?: string;
    dueDate: Date;
    priority: "high" | "medium" | "low";
    status: "todo" | "in-progress" | "done";
    assignee?: string;
}

interface CalendarEvent {
    id: string;
    title: string;
    start: Date;
    end: Date;
    meeting?: Meeting;
    task?: Task;
    color: string;
    type: "meeting" | "task";
}

// Demo tasks for the calendar
const demoTasks: Task[] = [
    {
        id: "t1",
        title: "Review Q1 Product Roadmap",
        description: "Review and finalize the Q1 product roadmap document",
        dueDate: new Date(new Date().setDate(new Date().getDate() + 2)),
        priority: "high",
        status: "todo",
        assignee: "Sarah Chen",
    },
    {
        id: "t2",
        title: "Prepare Client Presentation",
        description: "Create presentation slides for upcoming client meeting",
        dueDate: new Date(new Date().setDate(new Date().getDate() + 5)),
        priority: "high",
        status: "in-progress",
        assignee: "Mike Johnson",
    },
    {
        id: "t3",
        title: "Update API Documentation",
        description: "Document new API endpoints for emotion analysis",
        dueDate: new Date(new Date().setDate(new Date().getDate() + 7)),
        priority: "medium",
        status: "todo",
        assignee: "Alex Kumar",
    },
    {
        id: "t4",
        title: "Team Standup Meeting Prep",
        description: "Prepare agenda and talking points for team standup",
        dueDate: new Date(new Date().setDate(new Date().getDate() + 1)),
        priority: "low",
        status: "todo",
        assignee: "Priya Patel",
    },
    {
        id: "t5",
        title: "Code Review: Emotion Module",
        description: "Review pull request for emotion detection module",
        dueDate: new Date(new Date().setDate(new Date().getDate() + 3)),
        priority: "high",
        status: "todo",
        assignee: "Dev Team",
    },
    {
        id: "t6",
        title: "Update Meeting Notes Template",
        description: "Revise the meeting notes template based on feedback",
        dueDate: new Date(new Date().setDate(new Date().getDate() + 10)),
        priority: "low",
        status: "todo",
        assignee: "Sarah Chen",
    },
    {
        id: "t7",
        title: "Schedule Q2 Planning Session",
        description: "Coordinate with team to schedule Q2 planning meeting",
        dueDate: new Date(new Date().setDate(new Date().getDate() + 4)),
        priority: "medium",
        status: "in-progress",
        assignee: "Mike Johnson",
    },
];

export default function CalendarPage() {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [meetings, setMeetings] = useState<Meeting[]>(mockMeetings);
    const [tasks, setTasks] = useState<Task[]>(demoTasks);
    const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
    const [selectedTask, setSelectedTask] = useState<Task | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        fetchMeetings();
    }, []);

    useEffect(() => {
        // Convert meetings to calendar events
        const meetingEvents: CalendarEvent[] = meetings.map((meeting) => ({
            id: meeting.id,
            title: meeting.title,
            start: new Date(meeting.date),
            end: new Date(new Date(meeting.date).getTime() + meeting.duration * 60000),
            meeting: meeting,
            color: getMeetingColor(meeting.title),
            type: "meeting",
        }));

        // Convert tasks to calendar events
        const taskEvents: CalendarEvent[] = tasks.map((task) => ({
            id: task.id,
            title: task.title,
            start: new Date(task.dueDate),
            end: new Date(task.dueDate),
            task: task,
            color: getTaskColor(task.priority),
            type: "task",
        }));

        // Combine all events
        setCalendarEvents([...meetingEvents, ...taskEvents]);
    }, [meetings, tasks]);

    const fetchMeetings = async () => {
        try {
            setLoading(true);
            const result = await apiClient.listMeetings();
            if (result.success && result.meetings) {
                // Transform API meetings to match our Meeting interface
                // For now, we'll use mock data until API structure is confirmed
                setMeetings(mockMeetings);
            }
        } catch (error: any) {
            console.error("Failed to fetch meetings:", error);
            // Use mock data on error
            setMeetings(mockMeetings);
        } finally {
            setLoading(false);
        }
    };

    const getMeetingColor = (title: string) => {
        const hash = title.split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
        
        const colors = [
            '#9333EA', // Purple
            '#3B82F6', // Blue
            '#10B981', // Green
            '#F59E0B', // Amber
            '#EF4444', // Red
            '#8B5CF6', // Violet
            '#06B6D4', // Cyan
            '#EC4899', // Pink
        ];
        
        return colors[Math.abs(hash) % colors.length];
    };

    const getTaskColor = (priority: "high" | "medium" | "low") => {
        switch (priority) {
            case "high":
                return "#EF4444"; // Red
            case "medium":
                return "#F59E0B"; // Amber
            case "low":
                return "#10B981"; // Green
            default:
                return "#6B7280"; // Gray
        }
    };

    const getDaysInMonth = (date: Date) => {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const startingDayOfWeek = firstDay.getDay();

        const days = [];
        
        for (let i = 0; i < startingDayOfWeek; i++) {
            days.push(null);
        }
        
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        
        for (let day = 1; day <= daysInMonth; day++) {
            days.push(new Date(year, month, day));
        }
        
        return days;
    };

    const getEventsForDate = (date: Date) => {
        return calendarEvents.filter(event => {
            const eventStart = new Date(event.start);
            const eventEnd = new Date(event.end);
            eventStart.setHours(0, 0, 0, 0);
            eventEnd.setHours(23, 59, 59, 999);
            const checkDate = new Date(date);
            checkDate.setHours(0, 0, 0, 0);
            return checkDate >= eventStart && checkDate <= eventEnd;
        });
    };

    const openEventModal = (event: CalendarEvent) => {
        if (event.type === "meeting" && event.meeting) {
            setSelectedMeeting(event.meeting);
            setSelectedTask(null);
            setIsModalOpen(true);
        } else if (event.type === "task" && event.task) {
            setSelectedTask(event.task);
            setSelectedMeeting(null);
            setIsModalOpen(true);
        }
    };

    const formatDateHeader = (date: Date) => {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long'
        });
    };

    const navigateMonth = (direction: 'prev' | 'next') => {
        setCurrentDate(prev => {
            const newDate = new Date(prev);
            if (direction === 'prev') {
                newDate.setMonth(newDate.getMonth() - 1);
            } else {
                newDate.setMonth(newDate.getMonth() + 1);
            }
            return newDate;
        });
    };


    const monthDays = getDaysInMonth(currentDate);
    const upcomingEvents = calendarEvents.filter(e => e.start >= new Date()).slice(0, 5);

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
                    <p className="mt-4 text-muted-foreground">Loading your meetings calendar...</p>
                </div>
            </div>
        );
    }

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
                            <Link href="/calendar" className="text-sm font-medium text-purple-600">
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
                        <div className="flex items-center space-x-3 mb-2">
                            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-600 rounded-lg flex items-center justify-center">
                                <CalendarIcon className="w-5 h-5 text-white" />
                            </div>
                            <h1 className="text-3xl font-bold">Meeting Calendar</h1>
                        </div>
                        <p className="text-muted-foreground">View and manage your scheduled meetings</p>
                    </div>
                    <Button className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700">
                        <Plus className="h-4 w-4 mr-2" />
                        Schedule Meeting
                    </Button>
                </div>

                {/* Calendar Container */}
                <div className="bg-card rounded-2xl shadow-lg border overflow-hidden mb-8">
                    {/* Calendar Controls */}
                    <div className="flex justify-between items-center p-6 bg-muted/50 border-b">
                        <div className="flex items-center space-x-4">
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => navigateMonth('prev')}
                                className="hover:bg-muted"
                            >
                                <ChevronLeft className="h-5 w-5" />
                            </Button>
                            <h2 className="text-2xl font-bold">{formatDateHeader(currentDate)}</h2>
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => navigateMonth('next')}
                                className="hover:bg-muted"
                            >
                                <ChevronRight className="h-5 w-5" />
                            </Button>
                        </div>
                    </div>

                    {/* Calendar Grid */}
                    <div className="p-6">
                        <div className="grid grid-cols-7 gap-2 mb-4">
                            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                                <div key={day} className="p-3 text-center text-sm font-semibold text-muted-foreground bg-muted/50 rounded-lg">
                                    {day}
                                </div>
                            ))}
                        </div>
                        
                        <div className="grid grid-cols-7 gap-2">
                            {monthDays.map((day, index) => {
                                if (!day) {
                                    return <div key={index} className="p-2 h-32 rounded-lg"></div>;
                                }
                                
                                const dayEvents = getEventsForDate(day);
                                const isToday = day.toDateString() === new Date().toDateString();
                                
                                return (
                                    <div
                                        key={index}
                                        className={`p-3 h-32 border-2 rounded-lg bg-card hover:bg-muted/50 transition-all duration-200 relative overflow-hidden ${
                                            isToday ? 'border-purple-500 bg-purple-50 dark:bg-purple-950/20 shadow-md' : 'border-border'
                                        }`}
                                    >
                                        <div className={`text-sm font-semibold mb-2 ${
                                            isToday ? 'text-purple-600 dark:text-purple-400' : 'text-foreground'
                                        }`}>
                                            {day.getDate()}
                                        </div>
                                        <div className="space-y-1 overflow-y-auto max-h-20">
                                            {dayEvents.slice(0, 2).map(event => (
                                                <div
                                                    key={event.id}
                                                    onClick={() => openEventModal(event)}
                                                    className={`text-xs p-1.5 rounded-md cursor-pointer hover:opacity-90 transition-all duration-200 font-medium shadow-sm truncate flex items-center gap-1 ${
                                                        event.type === "task" 
                                                            ? "text-white border-l-2" 
                                                            : "text-white"
                                                    }`}
                                                    style={{ 
                                                        backgroundColor: event.color,
                                                        borderLeftColor: event.type === "task" ? "#FFFFFF" : "transparent",
                                                        borderLeftWidth: event.type === "task" ? "3px" : "0px"
                                                    }}
                                                    title={event.title}
                                                >
                                                    {event.type === "task" && (
                                                        <CheckSquare className="h-3 w-3 flex-shrink-0" />
                                                    )}
                                                    {event.type === "meeting" && (
                                                        <Video className="h-3 w-3 flex-shrink-0" />
                                                    )}
                                                    <span className="truncate">{event.title}</span>
                                                </div>
                                            ))}
                                            {dayEvents.length > 2 && (
                                                <div className="text-xs text-muted-foreground bg-muted p-1 rounded text-center font-medium">
                                                    +{dayEvents.length - 2} more
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Statistics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    {/* Meeting Statistics */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Meeting Statistics</CardTitle>
                            <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-muted-foreground">Total Meetings:</span>
                                    <span className="font-bold text-xl">{meetings.length}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-muted-foreground">Total Tasks:</span>
                                    <span className="font-bold text-xl text-green-600">{tasks.length}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-muted-foreground">This Month:</span>
                                    <span className="font-bold text-xl text-purple-600">
                                        {calendarEvents.filter(e => {
                                            const eventDate = new Date(e.start);
                                            return eventDate.getMonth() === currentDate.getMonth() && 
                                                   eventDate.getFullYear() === currentDate.getFullYear();
                                        }).length}
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-muted-foreground">Upcoming:</span>
                                    <span className="font-bold text-xl text-blue-600">
                                        {calendarEvents.filter(e => e.start >= new Date()).length}
                                    </span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Upcoming Meetings */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Upcoming Events</CardTitle>
                            <Clock className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {upcomingEvents.length > 0 ? (
                                    upcomingEvents.slice(0, 3).map(event => (
                                        <div 
                                            key={event.id} 
                                            className="flex items-center space-x-3 p-2 bg-muted/50 rounded-lg hover:bg-muted transition-colors cursor-pointer"
                                            onClick={() => openEventModal(event)}
                                        >
                                            <div
                                                className={`w-3 h-3 rounded-full flex-shrink-0 ${
                                                    event.type === "task" ? "rounded-sm" : ""
                                                }`}
                                                style={{ backgroundColor: event.color }}
                                            ></div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-1.5">
                                                    {event.type === "task" && (
                                                        <CheckSquare className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                                                    )}
                                                    {event.type === "meeting" && (
                                                        <Video className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                                                    )}
                                                    <span className="font-semibold text-sm truncate">{event.title}</span>
                                                </div>
                                                <div className="text-xs text-muted-foreground">
                                                    {format(event.start, "PPp")}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center py-4">
                                        <p className="text-sm text-muted-foreground">No upcoming events</p>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Quick Actions */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
                            <Plus className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <Button variant="outline" className="w-full justify-start" asChild>
                                <Link href="/bot-manager">
                                    <Video className="h-4 w-4 mr-2" />
                                    Start Meeting Bot
                                </Link>
                            </Button>
                            <Button variant="outline" className="w-full justify-start" asChild>
                                <Link href="/dashboard">
                                    <FileText className="h-4 w-4 mr-2" />
                                    View Dashboard
                                </Link>
                            </Button>
                            <Button variant="outline" className="w-full justify-start" asChild>
                                <Link href="/analytics/emotion">
                                    <Brain className="h-4 w-4 mr-2" />
                                    Emotion Analytics
                                </Link>
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Event Details Modal */}
            <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    {selectedMeeting && (
                        <>
                            <DialogHeader>
                                <DialogTitle className="text-2xl flex items-center gap-2">
                                    <Video className="h-5 w-5" />
                                    {selectedMeeting.title}
                                </DialogTitle>
                                <DialogDescription>
                                    Meeting details and information
                                </DialogDescription>
                            </DialogHeader>
                            
                            <div className="space-y-6 mt-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4 text-muted-foreground" />
                                        <div>
                                            <div className="text-sm text-muted-foreground">Date & Time</div>
                                            <div className="font-medium">{format(new Date(selectedMeeting.date), "PPp")}</div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4 text-muted-foreground" />
                                        <div>
                                            <div className="text-sm text-muted-foreground">Duration</div>
                                            <div className="font-medium">{selectedMeeting.duration} minutes</div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Users className="h-4 w-4 text-muted-foreground" />
                                        <div>
                                            <div className="text-sm text-muted-foreground">Participants</div>
                                            <div className="font-medium">{selectedMeeting.participants.length} people</div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Brain className="h-4 w-4 text-muted-foreground" />
                                        <div>
                                            <div className="text-sm text-muted-foreground">Engagement Score</div>
                                            <div className="font-medium">{selectedMeeting.emotionData.overallScore}/10</div>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-semibold mb-2">Participants</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedMeeting.participants.map((participant, i) => (
                                            <Badge key={i} variant="secondary">
                                                {participant}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>

                                {selectedMeeting.summary && (
                                    <div>
                                        <h4 className="font-semibold mb-2">Summary</h4>
                                        <p className="text-sm text-muted-foreground">{selectedMeeting.summary}</p>
                                    </div>
                                )}

                                {selectedMeeting.decisions && selectedMeeting.decisions.length > 0 && (
                                    <div>
                                        <h4 className="font-semibold mb-2">Key Decisions</h4>
                                        <ul className="space-y-1">
                                            {selectedMeeting.decisions.map((decision, i) => (
                                                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-purple-600 flex-shrink-0"></span>
                                                    {decision}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                <div className="flex justify-end gap-2 pt-4 border-t">
                                    <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                                        Close
                                    </Button>
                                    <Button className="bg-gradient-to-r from-purple-600 to-blue-600" asChild>
                                        <Link href={`/meetings/${selectedMeeting.id}`}>
                                            View Details
                                            <ArrowRight className="h-4 w-4 ml-2" />
                                        </Link>
                                    </Button>
                                </div>
                            </div>
                        </>
                    )}
                    {selectedTask && (
                        <>
                            <DialogHeader>
                                <DialogTitle className="text-2xl flex items-center gap-2">
                                    <CheckSquare className="h-5 w-5" />
                                    {selectedTask.title}
                                </DialogTitle>
                                <DialogDescription>
                                    Task details and information
                                </DialogDescription>
                            </DialogHeader>
                            
                            <div className="space-y-6 mt-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4 text-muted-foreground" />
                                        <div>
                                            <div className="text-sm text-muted-foreground">Due Date</div>
                                            <div className="font-medium">{format(selectedTask.dueDate, "PPp")}</div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Badge 
                                            variant="outline" 
                                            className={
                                                selectedTask.priority === "high" 
                                                    ? "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20"
                                                    : selectedTask.priority === "medium"
                                                    ? "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20"
                                                    : "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20"
                                            }
                                        >
                                            {selectedTask.priority} priority
                                        </Badge>
                                    </div>
                                    {selectedTask.assignee && (
                                        <div className="flex items-center gap-2">
                                            <Users className="h-4 w-4 text-muted-foreground" />
                                            <div>
                                                <div className="text-sm text-muted-foreground">Assignee</div>
                                                <div className="font-medium">{selectedTask.assignee}</div>
                                            </div>
                                        </div>
                                    )}
                                    <div className="flex items-center gap-2">
                                        <Badge variant="secondary">
                                            {selectedTask.status}
                                        </Badge>
                                    </div>
                                </div>

                                {selectedTask.description && (
                                    <div>
                                        <h4 className="font-semibold mb-2">Description</h4>
                                        <p className="text-sm text-muted-foreground">{selectedTask.description}</p>
                                    </div>
                                )}

                                <div className="flex justify-end gap-2 pt-4 border-t">
                                    <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                                        Close
                                    </Button>
                                    <Button className="bg-gradient-to-r from-purple-600 to-blue-600" asChild>
                                        <Link href="/tasks">
                                            View in Tasks
                                            <ArrowRight className="h-4 w-4 ml-2" />
                                        </Link>
                                    </Button>
                                </div>
                            </div>
                        </>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
