"use client";

import Link from "next/link";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/theme-toggle";
import { Brain, Calendar as CalendarIcon, Plus } from "lucide-react";
import { mockMeetings, ActionItem } from "@/lib/mock-data";
import { DndContext, DragEndEvent, closestCorners } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy, useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { format } from "date-fns";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

// Extract all action items from meetings
const allTasks: ActionItem[] = mockMeetings.flatMap((m) => m.actionItems);

function TaskCard({ task }: { task: ActionItem }) {
    const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: task.id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
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

    return (
        <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
            <Card className="mb-3 cursor-move hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium text-sm">{task.task}</h4>
                        <Badge variant="outline" className={getPriorityColor(task.priority)}>
                            {task.priority}
                        </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                        <CalendarIcon className="h-3 w-3" />
                        {format(new Date(task.dueDate), "PP")}
                    </div>
                    <div className="flex items-center gap-2">
                        <Avatar className="h-6 w-6">
                            <AvatarFallback className="text-xs">
                                {task.owner.split(" ").map((n) => n[0]).join("")}
                            </AvatarFallback>
                        </Avatar>
                        <span className="text-xs text-muted-foreground">{task.owner}</span>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

export default function TasksPage() {
    const [tasks, setTasks] = useState<Record<string, ActionItem[]>>({
        todo: allTasks.filter((t) => t.status === "todo"),
        "in-progress": allTasks.filter((t) => t.status === "in-progress"),
        done: allTasks.filter((t) => t.status === "done"),
    });
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [newTask, setNewTask] = useState({
        task: "",
        owner: "",
        dueDate: "",
        priority: "medium" as "high" | "medium" | "low",
        status: "todo" as "todo" | "in-progress" | "done",
    });

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;
        if (!over) return;

        // In a real app, this would update the task status
        console.log(`Moved task ${active.id} to ${over.id}`);
    };

    const handleCreateTask = () => {
        if (!newTask.task.trim() || !newTask.owner.trim() || !newTask.dueDate) {
            toast.error("Please fill in all required fields");
            return;
        }

        const taskId = `task-${Date.now()}`;
        const newTaskItem: ActionItem = {
            id: taskId,
            task: newTask.task,
            owner: newTask.owner,
            dueDate: newTask.dueDate,
            priority: newTask.priority,
            status: newTask.status,
            meetingId: "",
        };

        setTasks((prev) => ({
            ...prev,
            [newTask.status]: [...prev[newTask.status], newTaskItem],
        }));

        // Reset form
        setNewTask({
            task: "",
            owner: "",
            dueDate: "",
            priority: "medium",
            status: "todo",
        });
        setIsDialogOpen(false);
        toast.success("Task created successfully!");
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
                            <Link href="/tasks" className="text-sm font-medium text-purple-600">
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
                        <h1 className="text-3xl font-bold mb-2">Task Board</h1>
                        <p className="text-muted-foreground">Manage tasks extracted from your meetings</p>
                    </div>
                    <Button 
                        className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                        onClick={() => setIsDialogOpen(true)}
                    >
                        <Plus className="h-4 w-4 mr-2" />
                        New Task
                    </Button>
                </div>

                {/* Kanban Board */}
                <DndContext collisionDetection={closestCorners} onDragEnd={handleDragEnd}>
                    <div className="grid md:grid-cols-3 gap-6">
                        {/* To Do Column */}
                        <div>
                            <div className="mb-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-semibold">To Do</h3>
                                    <Badge variant="secondary">{tasks.todo.length}</Badge>
                                </div>
                                <div className="h-1 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full" />
                            </div>
                            <SortableContext items={tasks.todo.map((t) => t.id)} strategy={verticalListSortingStrategy}>
                                {tasks.todo.map((task) => (
                                    <TaskCard key={task.id} task={task} />
                                ))}
                            </SortableContext>
                        </div>

                        {/* In Progress Column */}
                        <div>
                            <div className="mb-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-semibold">In Progress</h3>
                                    <Badge variant="secondary">{tasks["in-progress"].length}</Badge>
                                </div>
                                <div className="h-1 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" />
                            </div>
                            <SortableContext items={tasks["in-progress"].map((t) => t.id)} strategy={verticalListSortingStrategy}>
                                {tasks["in-progress"].map((task) => (
                                    <TaskCard key={task.id} task={task} />
                                ))}
                            </SortableContext>
                        </div>

                        {/* Done Column */}
                        <div>
                            <div className="mb-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="font-semibold">Done</h3>
                                    <Badge variant="secondary">{tasks.done.length}</Badge>
                                </div>
                                <div className="h-1 bg-gradient-to-r from-green-500 to-green-600 rounded-full" />
                            </div>
                            <SortableContext items={tasks.done.map((t) => t.id)} strategy={verticalListSortingStrategy}>
                                {tasks.done.map((task) => (
                                    <TaskCard key={task.id} task={task} />
                                ))}
                            </SortableContext>
                        </div>
                    </div>
                </DndContext>

                {/* Integration Section */}
                <Card className="mt-8">
                    <CardHeader>
                        <CardTitle>Integrations</CardTitle>
                        <CardDescription>Sync tasks with your favorite project management tools</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid md:grid-cols-3 gap-4">
                            <Button variant="outline" className="h-20">
                                <div className="text-center">
                                    <div className="font-semibold mb-1">Jira</div>
                                    <div className="text-xs text-muted-foreground">Connect to Jira</div>
                                </div>
                            </Button>
                            <Button variant="outline" className="h-20">
                                <div className="text-center">
                                    <div className="font-semibold mb-1">Trello</div>
                                    <div className="text-xs text-muted-foreground">Connect to Trello</div>
                                </div>
                            </Button>
                            <Button variant="outline" className="h-20">
                                <div className="text-center">
                                    <div className="font-semibold mb-1">Asana</div>
                                    <div className="text-xs text-muted-foreground">Connect to Asana</div>
                                </div>
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* New Task Dialog */}
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Create New Task</DialogTitle>
                        <DialogDescription>
                            Add a new task to your task board
                        </DialogDescription>
                    </DialogHeader>
                    
                    <div className="space-y-4 mt-4">
                        <div className="space-y-2">
                            <Label htmlFor="task">Task Title *</Label>
                            <Input
                                id="task"
                                placeholder="Enter task description"
                                value={newTask.task}
                                onChange={(e) => setNewTask({ ...newTask, task: e.target.value })}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="owner">Assignee *</Label>
                            <Input
                                id="owner"
                                placeholder="Enter assignee name"
                                value={newTask.owner}
                                onChange={(e) => setNewTask({ ...newTask, owner: e.target.value })}
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="dueDate">Due Date *</Label>
                                <Input
                                    id="dueDate"
                                    type="date"
                                    value={newTask.dueDate}
                                    onChange={(e) => setNewTask({ ...newTask, dueDate: e.target.value })}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="priority">Priority</Label>
                                <Select
                                    value={newTask.priority}
                                    onValueChange={(value: "high" | "medium" | "low") =>
                                        setNewTask({ ...newTask, priority: value })
                                    }
                                >
                                    <SelectTrigger id="priority">
                                        <SelectValue placeholder="Select priority" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="high">High</SelectItem>
                                        <SelectItem value="medium">Medium</SelectItem>
                                        <SelectItem value="low">Low</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="status">Status</Label>
                            <Select
                                value={newTask.status}
                                onValueChange={(value: "todo" | "in-progress" | "done") =>
                                    setNewTask({ ...newTask, status: value })
                                }
                            >
                                <SelectTrigger id="status">
                                    <SelectValue placeholder="Select status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="todo">To Do</SelectItem>
                                    <SelectItem value="in-progress">In Progress</SelectItem>
                                    <SelectItem value="done">Done</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="flex justify-end gap-2 pt-4 border-t">
                            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                                Cancel
                            </Button>
                            <Button 
                                className="bg-gradient-to-r from-purple-600 to-blue-600"
                                onClick={handleCreateTask}
                            >
                                Create Task
                            </Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}
