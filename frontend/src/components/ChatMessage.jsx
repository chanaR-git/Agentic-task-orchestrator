import React, { useState, useEffect, useRef } from 'react';
import { Send, Trash2, CheckCircle, Plus, List, Bot, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ChatMessage = ({ message }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
  >
    <div className={`flex items-start max-w-[80%] ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`p-2 rounded-full ${message.sender === 'user' ? 'bg-blue-500 ml-2' : 'bg-purple-500 mr-2'}`}>
        {message.sender === 'user' ? <User size={20} color="white" /> : <Bot size={20} color="white" />}
      </div>
      <div className={`p-3 rounded-2xl shadow-sm ${
        message.sender === 'user' 
          ? 'bg-blue-600 text-white rounded-tr-none' 
          : 'bg-white text-gray-800 rounded-tl-none border border-gray-100'
      }`}>
        <p className="text-sm leading-relaxed">{message.text}</p>
      </div>
    </div>
  </motion.div>
);
export default ChatMessage;