import React, { useState, useEffect, useRef } from 'react';
import { Send, List, Bot, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatMessage from './ChatMessage';

const TaskManagerBot = () => {
  const [messages, setMessages] = useState([
    { id: 1, text: "שלום! אני סוכן ניהול המשימות שלך. איך אוכל לעזור?", sender: 'bot' }
  ]);
  const [input, setInput] = useState('');
  const [tasks, setTasks] = useState([]); 
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  // גלילה אוטומטית לסוף הצ'אט
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    
    // הוספת הודעת המשתמש למסך
    setMessages(prev => [...prev, { id: Date.now(), text: userMessage, sender: 'user' }]);
    setInput('');
    
    // שליחה לשרת
    await processCommand(userMessage);
  };

  const processCommand = async (command) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: command }),
      });

      if (!response.ok) throw new Error('השרת החזיר שגיאה');

      const data = await response.json();

      // עדכון הצ'אט עם התשובה מהסוכן (שדה response ב-JSON)
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        text: data.response, 
        sender: 'bot' 
      }]);

      // הערה: אם הסוכן שלך מעדכן משימות, כדאי שה-API יחזיר גם את רשימת המשימות המעודכנת
      // ובמקרה כזה נעדכן כאן: if(data.tasks) setTasks(data.tasks);

    } catch (error) {
      console.error("API Error:", error);
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        text: "מצטער, חלה שגיאה בתקשורת עם הסוכן. וודא שהשרת רץ.", 
        sender: 'bot' 
      }]);
    } finally {
      setIsLoading(false);
    }
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
          {tasks.length === 0 ? (
            <p className="text-gray-400 text-sm text-center mt-10 italic">אין משימות פעילות</p>
          ) : (
            <AnimatePresence>
              {tasks.map(task => (
                <motion.div
                  key={task.id}
                  initial={{ x: 20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  className="p-3 mb-2 bg-gray-50 rounded-xl border border-gray-100"
                >
                  <span className="text-sm text-gray-700">{task.text}</span>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-col flex-1 max-w-4xl mx-auto w-full relative">
        <header className="p-4 bg-white/80 backdrop-blur-md border-b sticky top-0 z-10 flex justify-between items-center px-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-tr from-purple-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg">
              <Bot color="white" size={24} />
            </div>
            <div>
              <h1 className="font-bold text-gray-800">TaskBot Agent</h1>
              <span className="text-xs text-green-500 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> מחובר לסוכן
              </span>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50">
          {messages.map(msg => <ChatMessage key={msg.id} message={msg} />)}
          
          {/* בועת טעינה (Thinking) */}
          {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="bg-white p-3 rounded-2xl border border-gray-100 flex items-center gap-2 text-gray-400 text-sm">
                <Loader2 size={16} className="animate-spin" />
                הסוכן מעבד את הבקשה...
              </div>
            </motion.div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="p-6 bg-white border-t">
          <form onSubmit={handleSend} className="relative flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="כתוב הודעה לסוכן..."
              className="w-full p-4 pr-12 rounded-2xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-400 bg-gray-50"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading}
              className="absolute left-3 p-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-all disabled:bg-gray-300"
            >
              <Send size={20} className="rotate-180" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TaskManagerBot;