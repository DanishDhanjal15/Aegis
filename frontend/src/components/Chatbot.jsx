import React, { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Bot, User, Minimize2 } from "lucide-react";
import { sendMessageToChatbot } from "../api";

const Chatbot = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([
        { role: "bot", content: "Hello! I'm Aegis AI. I can help you with your network security. Try asking 'How many devices are connected?'" }
    ]);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput("");
        setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
        setLoading(true);

        try {
            const result = await sendMessageToChatbot(userMessage);
            setMessages((prev) => [...prev, { role: "bot", content: result.reply }]);
        } catch (error) {
            setMessages((prev) => [...prev, { role: "bot", content: "I'm sorry, I'm having trouble responding right now." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-6 right-6 z-50">
            {/* Floating Button */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="w-14 h-14 bg-slate-900 dark:bg-white text-white dark:text-black rounded-full shadow-lg flex items-center justify-center hover:scale-110 transition-transform duration-200 group"
                >
                    <MessageSquare size={24} className="group-hover:rotate-12 transition-transform" />
                    <div className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full border-2 border-white dark:border-zinc-950 animate-pulse"></div>
                </button>
            )}

            {/* Chat Window */}
            {isOpen && (
                <div className="w-80 sm:w-96 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 dark:border-zinc-800/50 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-300 ring-1 ring-black/5 dark:ring-white/5">
                    {/* Header */}
                    <div className="p-4 bg-gradient-to-r from-slate-900 to-slate-800 dark:from-zinc-800 dark:to-zinc-900 text-white flex items-center justify-between border-b border-white/10">
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 bg-blue-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                                <Bot size={20} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-sm tracking-tight text-white">Aegis Assistant</h3>
                                <div className="flex items-center gap-1.5">
                                    <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></div>
                                    <p className="text-[10px] text-blue-200 font-medium uppercase tracking-wider">Online</p>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-1.5 hover:bg-white/10 rounded-lg transition-colors border border-transparent hover:border-white/10"
                                title="Minimize"
                            >
                                <Minimize2 size={16} />
                            </button>
                        </div>
                    </div>

                    {/* Messages Area */}
                    <div className="flex-1 h-96 overflow-y-auto p-4 space-y-4 bg-transparent custom-scrollbar">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-300`}
                                style={{ animationDelay: `${idx * 50}ms` }}
                            >
                                <div className={`flex gap-2 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-1 shadow-sm ${msg.role === "user" ? "bg-slate-200 dark:bg-zinc-700" : "bg-blue-100 dark:bg-blue-900/30"
                                        }`}>
                                        {msg.role === "user" ? <User size={16} className="text-slate-600 dark:text-zinc-400" /> : <Bot size={16} className="text-blue-600 dark:text-blue-400" />}
                                    </div>
                                    <div className={`p-3.5 rounded-2xl text-[13px] leading-relaxed ${msg.role === "user"
                                        ? "bg-slate-900 text-white rounded-tr-none shadow-md shadow-slate-900/10"
                                        : "bg-white dark:bg-zinc-800 text-slate-700 dark:text-zinc-300 border border-gray-100 dark:border-zinc-700/50 rounded-tl-none shadow-sm"
                                        }`}>
                                        {msg.content}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex justify-start animate-in fade-in duration-200">
                                <div className="flex gap-2 max-w-[85%]">
                                    <div className="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                                        <Bot size={16} className="text-blue-600 dark:text-blue-400" />
                                    </div>
                                    <div className="bg-white dark:bg-zinc-800 p-3.5 rounded-2xl rounded-tl-none border border-gray-100 dark:border-zinc-700/50 shadow-sm flex gap-1 items-center">
                                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></div>
                                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <form onSubmit={handleSend} className="p-4 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md border-t border-gray-200 dark:border-zinc-800 flex gap-2">
                        <div className="relative flex-1">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Type a message..."
                                className="w-full bg-gray-100 dark:bg-zinc-800/80 border-none rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500/50 dark:text-white transition-all placeholder:text-slate-400 dark:placeholder:text-zinc-500"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={!input.trim() || loading}
                            className="px-4 bg-slate-900 dark:bg-white text-white dark:text-black rounded-xl hover:bg-slate-800 dark:hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-slate-900/10 dark:shadow-white/5 flex items-center justify-center"
                        >
                            <Send size={18} className={input.trim() ? "translate-x-0.5 -translate-y-0.5" : ""} />
                        </button>
                    </form>
                </div>
            )}
        </div>
    );
};

export default Chatbot;
