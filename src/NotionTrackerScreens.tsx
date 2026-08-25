import React, { useState } from 'react';

/**
 * Notion Tracker - Premium Responsive Web Screens
 * --------------------------------------------------
 * This single-file React component contains both the "Registration Page" and the
 * "OTP Login Page" for the Notion Tracker application.
 * 
 * Styled using: Tailwind CSS
 * Language: TypeScript
 * Design Aesthetic: Classic Notion Monochrome (Greys, Blacks, Whites)
 * Accessibility: Semantic HTML, proper contrast (WCAG AA), screen-reader friendly labels and ARIA attributes.
 */

// Define Types for our Screens
type ActiveScreen = 'register' | 'otp';

export default function NotionTrackerScreens() {
  const [activeScreen, setActiveScreen] = useState<ActiveScreen>('register');
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    otpPhone: ''
  });

  // Handle Form Input Changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle Submit Actions
  const handleSubmit = (e: React.FormEvent, type: 'register' | 'otp') => {
    e.preventDefault();
    if (type === 'register') {
      alert(`Registration payload submitted:\n${JSON.stringify(formData, null, 2)}`);
    } else {
      alert(`OTP Login requested for: +91 ${formData.otpPhone}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#F1F3F5] text-[#1E293B] font-sans antialiased flex flex-col justify-between p-4 sm:p-6 md:p-8">
      
      {/* ── INTERACTIVE TEST TOGGLE (PERFECT FOR PRESENTATION DEMOS) ── */}
      <div className="max-w-md mx-auto mb-6 w-full bg-white border border-[#E2E8F0] shadow-sm rounded-lg p-3 flex justify-between items-center text-sm">
        <span className="font-semibold text-[#475569]">Demonstration Switcher:</span>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveScreen('register')}
            className={`px-3 py-1.5 rounded-md font-medium transition ${
              activeScreen === 'register'
                ? 'bg-[#1E293B] text-white shadow-sm'
                : 'bg-[#F8FAFC] text-[#64748B] hover:bg-[#F1F5F9]'
            }`}
            aria-label="Switch to Registration Screen"
          >
            Registration
          </button>
          <button
            onClick={() => setActiveScreen('otp')}
            className={`px-3 py-1.5 rounded-md font-medium transition ${
              activeScreen === 'otp'
                ? 'bg-[#1E293B] text-white shadow-sm'
                : 'bg-[#F8FAFC] text-[#64748B] hover:bg-[#F1F5F9]'
            }`}
            aria-label="Switch to OTP Login Screen"
          >
            OTP Login
          </button>
        </div>
      </div>

      {/* ── MAIN PAGES CONTAINER ── */}
      <main className="flex-1 flex items-center justify-center w-full max-w-6xl mx-auto py-4">
        
        {activeScreen === 'register' ? (
          /* ==========================================
             SCREEN 1: REGISTRATION PAGE
             ========================================== */
          <div 
            className="w-full bg-white rounded-xl shadow-xl border border-[#E2E8F0] overflow-hidden grid grid-cols-1 md:grid-cols-12 min-h-[600px] animate-fade-in"
            role="region" 
            aria-label="User Registration Section"
          >
            {/* Left Panel (Darker Grey Background) */}
            <div className="md:col-span-5 bg-[#1F2937] p-8 md:p-12 flex flex-col justify-between text-white relative">
              
              {/* Subtle background pattern */}
              <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none"></div>
              
              <div className="relative z-10">
                {/* Branded Icon Container */}
                <div className="w-12 h-12 rounded-full bg-[#374151] border border-[#4B5563] flex items-center justify-center mb-8 shadow-inner">
                  <img 
                    src="logo.png" 
                    alt="Notion Tracker Celtic Knot Logo" 
                    className="w-8 h-8 object-contain rounded-full"
                  />
                </div>

                <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
                  Join Notion Tracker
                </h1>
                <p className="text-[#9CA3AF] text-base leading-relaxed mb-10">
                  Register once to sync your workspace and track your progress.
                </p>

                {/* Feature Bullet List with circular icons */}
                <ul className="space-y-6" aria-label="Notion Tracker Core Features">
                  <li className="flex items-start gap-4">
                    <span 
                      className="flex-shrink-0 w-6 h-6 rounded-full bg-[#374151] border border-[#4B5563] flex items-center justify-center text-xs font-semibold text-white"
                      aria-hidden="true"
                    >
                      ✓
                    </span>
                    <span className="text-[#D1D5DB] text-sm md:text-base">
                      Sync seamlessly with Notion databases
                    </span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span 
                      className="flex-shrink-0 w-6 h-6 rounded-full bg-[#374151] border border-[#4B5563] flex items-center justify-center text-xs font-semibold text-white"
                      aria-hidden="true"
                    >
                      ✓
                    </span>
                    <span className="text-[#D1D5DB] text-sm md:text-base">
                      Organize your daily tasks
                    </span>
                  </li>
                  <li className="flex items-start gap-4">
                    <span 
                      className="flex-shrink-0 w-6 h-6 rounded-full bg-[#374151] border border-[#4B5563] flex items-center justify-center text-xs font-semibold text-white"
                      aria-hidden="true"
                    >
                      ✓
                    </span>
                    <span className="text-[#D1D5DB] text-sm md:text-base">
                      Monitor your productivity metrics
                    </span>
                  </li>
                </ul>
              </div>

              {/* Left Panel Footer */}
              <div className="mt-12 md:mt-0 relative z-10">
                <span className="text-xs text-[#9CA3AF] font-mono tracking-wider uppercase">
                  Enterprise-Grade Operations
                </span>
              </div>
            </div>

            {/* Right Panel (White Background) */}
            <div className="md:col-span-7 p-8 md:p-12 lg:p-16 flex flex-col justify-center">
              <div className="max-w-md mx-auto w-full">
                <h2 className="text-2xl font-bold text-[#111827] tracking-tight mb-2">
                  Create Your Account
                </h2>
                <p className="text-[#6B7280] text-sm mb-8">
                  Register to access your dashboard.
                </p>

                {/* Form Elements */}
                <form onSubmit={(e) => handleSubmit(e, 'register')} className="space-y-5">
                  {/* First & Last Name Two-Column Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="flex flex-col space-y-1.5">
                      <label 
                        htmlFor="firstName" 
                        className="text-xs font-semibold text-[#374151] uppercase tracking-wider"
                      >
                        First Name
                      </label>
                      <input
                        type="text"
                        id="firstName"
                        name="firstName"
                        required
                        value={formData.firstName}
                        onChange={handleInputChange}
                        placeholder="John"
                        className="px-3 py-2 border border-[#D1D5DB] rounded-md text-sm bg-white placeholder-[#9CA3AF] focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition"
                      />
                    </div>
                    <div className="flex flex-col space-y-1.5">
                      <label 
                        htmlFor="lastName" 
                        className="text-xs font-semibold text-[#374151] uppercase tracking-wider"
                      >
                        Last Name
                      </label>
                      <input
                        type="text"
                        id="lastName"
                        name="lastName"
                        required
                        value={formData.lastName}
                        onChange={handleInputChange}
                        placeholder="Doe"
                        className="px-3 py-2 border border-[#D1D5DB] rounded-md text-sm bg-white placeholder-[#9CA3AF] focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition"
                      />
                    </div>
                  </div>

                  {/* Email Input */}
                  <div className="flex flex-col space-y-1.5">
                    <label 
                      htmlFor="email" 
                      className="text-xs font-semibold text-[#374151] uppercase tracking-wider"
                    >
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      required
                      value={formData.email}
                      onChange={handleInputChange}
                      placeholder="john.doe@company.com"
                      className="px-3 py-2 border border-[#D1D5DB] rounded-md text-sm bg-white placeholder-[#9CA3AF] focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition w-full"
                    />
                  </div>

                  {/* Phone Input */}
                  <div className="flex flex-col space-y-1.5">
                    <label 
                      htmlFor="phone" 
                      className="text-xs font-semibold text-[#374151] uppercase tracking-wider"
                    >
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      required
                      value={formData.phone}
                      onChange={handleInputChange}
                      placeholder="+91 98765 43210"
                      className="px-3 py-2 border border-[#D1D5DB] rounded-md text-sm bg-white placeholder-[#9CA3AF] focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition w-full"
                    />
                  </div>

                  {/* Password Input */}
                  <div className="flex flex-col space-y-1.5">
                    <label 
                      htmlFor="password" 
                      className="text-xs font-semibold text-[#374151] uppercase tracking-wider"
                    >
                      Password
                    </label>
                    <input
                      type="password"
                      id="password"
                      name="password"
                      required
                      value={formData.password}
                      onChange={handleInputChange}
                      placeholder="••••••••••••"
                      className="px-3 py-2 border border-[#D1D5DB] rounded-md text-sm bg-white placeholder-[#9CA3AF] focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition w-full"
                    />
                  </div>

                  {/* Call To Action Button */}
                  <button
                    type="submit"
                    className="w-full mt-2 py-2.5 px-4 bg-[#1F2937] hover:bg-[#111827] text-white font-medium rounded-md text-sm shadow transition duration-150 flex items-center justify-center gap-2 group"
                  >
                    Create Account
                    <span className="transform group-hover:translate-x-1 transition-transform" aria-hidden="true">→</span>
                  </button>
                </form>

                {/* Footer Switcher */}
                <div className="mt-8 text-center">
                  <button
                    onClick={() => setActiveScreen('otp')}
                    className="text-xs font-medium text-[#4B5563] hover:text-black transition underline decoration-1 underline-offset-4"
                  >
                    Already have an account? Login with OTP
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* ==========================================
             SCREEN 2: OTP LOGIN PAGE
             ========================================== */
          <div 
            className="w-full max-w-md bg-white rounded-xl shadow-xl border border-[#E2E8F0] p-8 md:p-10 flex flex-col items-center justify-center min-h-[480px] animate-fade-in"
            role="region" 
            aria-label="OTP Authentication Section"
          >
            {/* Header Centered Image Logo & Title */}
            <div className="text-center mb-8 flex flex-col items-center">
              <div className="w-16 h-16 rounded-full bg-[#F3F4F6] border border-[#E5E7EB] flex items-center justify-center p-1.5 shadow-inner mb-3">
                <img 
                  src="logo.png" 
                  alt="Notion Tracker Celtic Knot Logo" 
                  className="w-12 h-12 object-contain rounded-full"
                />
              </div>
              <h1 className="text-xl font-bold text-[#111827] tracking-tight">
                Notion Tracker
              </h1>
            </div>

            {/* Greeting */}
            <div className="text-center mb-6">
              <h2 className="text-lg font-bold text-[#1F2937] mb-1">Welcome back</h2>
              <p className="text-xs text-[#6B7280]">Connect to your workspace</p>
            </div>

            {/* OTP Form */}
            <form onSubmit={(e) => handleSubmit(e, 'otp')} className="w-full space-y-5">
              <div className="flex flex-col space-y-1.5">
                <label 
                  htmlFor="otpPhone" 
                  className="text-xs font-semibold text-[#374151] uppercase tracking-wider"
                >
                  Mobile Number
                </label>
                
                {/* Prefix Combined input */}
                <div className="flex rounded-md border border-[#D1D5DB] focus-within:ring-1 focus-within:ring-black focus-within:border-black transition overflow-hidden">
                  {/* Fixed prefix box */}
                  <span 
                    className="inline-flex items-center px-3 bg-[#F3F4F6] border-r border-[#D1D5DB] text-xs font-medium text-[#4B5563] select-none"
                    aria-hidden="true"
                  >
                    IN +91
                  </span>
                  {/* Actual Input */}
                  <input
                    type="tel"
                    id="otpPhone"
                    name="otpPhone"
                    required
                    pattern="[0-9]{10}"
                    value={formData.otpPhone}
                    onChange={handleInputChange}
                    placeholder="98765 43210"
                    maxLength={10}
                    aria-label="10-digit mobile number input"
                    className="flex-1 px-3 py-2 text-sm bg-white placeholder-[#9CA3AF] focus:outline-none w-full"
                  />
                </div>
              </div>

              {/* Call to Action Button */}
              <button
                type="submit"
                className="w-full py-2.5 px-4 bg-[#4B5563] hover:bg-[#374151] text-white font-medium rounded-md text-sm shadow transition duration-150 flex items-center justify-center gap-2 group"
              >
                Get OTP
                <span className="transform group-hover:translate-x-1 transition-transform" aria-hidden="true">→</span>
              </button>
            </form>

            {/* Footer Text */}
            <div className="mt-8 text-center space-y-3">
              <p className="text-xs text-[#6B7280] leading-relaxed max-w-[280px] mx-auto">
                Simple access to your databases and tracking information.
              </p>
              <div>
                <button
                  onClick={() => setActiveScreen('register')}
                  className="text-xs font-bold text-[#374151] hover:text-black transition underline decoration-1 underline-offset-4"
                >
                  New User? Register Profile
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ── FOOTER DESIGN STANDARDS ── */}
      <footer className="w-full text-center py-4 mt-8 border-t border-[#E5E7EB] max-w-6xl mx-auto">
        <p className="text-[10px] text-[#9CA3AF] font-mono tracking-wider uppercase">
          Classic Notion Aesthetic • Highly Accessible & Responsive Grid • Mono-Chrome Edition
        </p>
      </footer>
    </div>
  );
}
