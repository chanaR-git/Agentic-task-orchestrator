import React, { useState, useEffect, useRef } from 'react';
import { Send, Trash2, CheckCircle, Plus, List, Bot, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatMessage from './ChatMessage';

const TaskManagerBot = () => {
  const [messages, setMessages] = useState([
    { id: 1, text: "שלום! אני עוזר המשימות שלך. איך אפשר לעזור היום? (נסה לכתוב: 'הוסף לקנות חלב')", sender: 'bot' }
  ]);
  const [input, setInput] = useState('');
  const [tasks, setTasks] = useState([]);
  const chatEndRef = useRef(null);

  // גלילה אוטומטית לסוף הצ'אט
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { id: Date.now(), text: userMessage, sender: 'user' }]);
    setInput('');

    // לוגיקה בסיסית של הצ'אטבוט (Parsing)
    setTimeout(() => {
      processCommand(userMessage);
    }, 600);
  };

  const processCommand = (command) => {
    let botResponse = "";
    
    if (command.includes("הוסף")) {
      const taskName = command.replace("הוסף", "").trim();
      if (taskName) {
        const newTask = { id: Date.now(), text: taskName, completed: false };
        setTasks(prev => [...prev, newTask]);
        botResponse = `הוספתי את המשימה: "${taskName}" לרשימה שלך.`;
      } else {
        botResponse = "מה תרצה שאוסיף? (לדוגמה: הוסף פגישה ב-10:00)";
      }
    } else if (command.includes("מחק הכל")) {
      setTasks([]);
      botResponse = "כל המשימות נמחקו.";
    } else if (command.includes("רשימה") || command.includes("מה יש לי")) {
      botResponse = tasks.length > 0 
        ? `יש לך ${tasks.length} משימות להיום.` 
        : "רשימת המשימות שלך ריקה כרגע.";
    } else {
      botResponse = "כאן התוכן שלך"; // Placeholder based on policy for generic responses
    }

    setMessages(prev => [...prev, { id: Date.now(), text: botResponse, sender: 'bot' }]);
  };

  const toggleTask = (id) => {
    setTasks(tasks.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
  };

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-right" dir="rtl">
      {/* Sidebar - Task List */}
      <div className="hidden md:flex flex-col w-80 bg-white border-l border-gray-200 p-6 shadow-sm">
        <div className="flex items-center mb-8 space-x-2 space-x-reverse text-purple-600 font-bold text-xl">
          <List size={24} />
          <span>המשימות שלי</span>
        </div>
        <div className="flex-1 overflow-y-auto">
          <AnimatePresence>
            {tasks.map(task => (
              <motion.div
                key={task.id}
                initial={{ x: 20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -20, opacity: 0 }}
                className="flex items-center justify-between p-3 mb-2 bg-gray-50 rounded-xl border border-gray-100 group hover:border-purple-200 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <button onClick={() => toggleTask(task.id)} className="text-gray-400 hover:text-green-500">
                    <CheckCircle size={20} className={task.completed ? "text-green-500 fill-current" : ""} />
                  </button>
                  <span className={`text-sm ${task.completed ? "line-through text-gray-400" : "text-gray-700"}`}>
                    {task.text}
                  </span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-col flex-1 max-w-4xl mx-auto w-full relative">
        {/* Header */}
        <header className="p-4 bg-white/80 backdrop-blur-md border-b sticky top-0 z-10 flex justify-between items-center px-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-tr from-purple-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg">
              <Bot color="white" size={24} />
            </div>
            <div>
              <h1 className="font-bold text-gray-800">TaskBot AI</h1>
              <span className="text-xs text-green-500 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> מחובר
              </span>
            </div>
          </div>
        </header>

        {/* Messages Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-fixed">
          {messages.map(msg => <ChatMessage key={msg.id} message={msg} />)}
          <div ref={chatEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-white border-t">
          <form onSubmit={handleSend} className="relative flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="כתוב כאן: הוסף לקנות לחם..."
              className="w-full p-4 pr-12 rounded-2xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent shadow-inner transition-all bg-gray-50"
            />
            <button
              type="submit"
              className="absolute left-3 p-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-transform active:scale-95 shadow-md"
            >
              <Send size={20} className="rotate-180" />
            </button>
          </form>
          <p className="text-[10px] text-center text-gray-400 mt-2 italic">
            טיפ: ניתן לומר "הוסף", "רשימה" או "מחק הכל"
          </p>
        </div>
      </div>
    </div>
  );
};

export default TaskManagerBot;