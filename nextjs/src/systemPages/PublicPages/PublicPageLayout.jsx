'use client';

import Header from "@/components/Header"


export default function PublicPageLayout({ children, authData, fullWidth = false }) {
  return (
    <>
      <div className="flex flex-col items-center justify-center">
        <Header authData={authData}/>
        <div 
          className={`flex flex-col items-center font-[family-name:var(--font-geist-sans)] p-2 md:p-10 ${fullWidth ? "md:max-w-full" : "md:max-w-300"}`} 
          style={{ width: '100%', minHeight: 'calc(100vh - 120px)' }}
        >
          {children(authData)}
        </div>
        
      </div>
      <div className="bg-[#7b003f] h-[30px] flex justify-center items-center text-white text-[0.7em]">
        Copyright © | All Rights Reserved | Vilnius university Kaunas faculty
      </div>
    </>
  );
}