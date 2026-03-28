"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export interface Task {
    id: string;
    title: string;
    description?: string;
    dueDate: Date;
    priority: "high" | "medium" | "low";
    status: "todo" | "in-progress" | "done";
    assignee?: string;
}

interface TaskContextType {
    tasks: Task[];
    addTask: (task: Task) => void;
    updateTask: (id: string, task: Partial<Task>) => void;
    deleteTask: (id: string) => void;
    updateTaskStatus: (id: string, status: "todo" | "in-progress" | "done") => void;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

const DEMO_TASKS: Task[] = [
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

export const TaskProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [tasks, setTasks] = useState<Task[]>([]);

    // Initialize tasks from localStorage or use demo tasks
    useEffect(() => {
        const storedTasks = localStorage.getItem("quantum_tasks");
        if (storedTasks) {
            try {
                const parsed = JSON.parse(storedTasks);
                // Convert date strings back to Date objects
                const tasksWithDates = parsed.map((t: any) => ({
                    ...t,
                    dueDate: new Date(t.dueDate),
                }));
                setTasks(tasksWithDates);
            } catch (e) {
                console.error("Failed to parse stored tasks:", e);
                setTasks(DEMO_TASKS);
            }
        } else {
            setTasks(DEMO_TASKS);
        }
    }, []);

    // Save tasks to localStorage whenever they change
    useEffect(() => {
        localStorage.setItem("quantum_tasks", JSON.stringify(tasks));
    }, [tasks]);

    const addTask = (task: Task) => {
        setTasks((prev) => [...prev, task]);
    };

    const updateTask = (id: string, updatedTask: Partial<Task>) => {
        setTasks((prev) =>
            prev.map((task) =>
                task.id === id ? { ...task, ...updatedTask } : task
            )
        );
    };

    const deleteTask = (id: string) => {
        setTasks((prev) => prev.filter((task) => task.id !== id));
    };

    const updateTaskStatus = (id: string, status: "todo" | "in-progress" | "done") => {
        updateTask(id, { status });
    };

    return (
        <TaskContext.Provider
            value={{
                tasks,
                addTask,
                updateTask,
                deleteTask,
                updateTaskStatus,
            }}
        >
            {children}
        </TaskContext.Provider>
    );
};

export const useTaskContext = () => {
    const context = useContext(TaskContext);
    if (!context) {
        throw new Error("useTaskContext must be used within TaskProvider");
    }
    return context;
};
