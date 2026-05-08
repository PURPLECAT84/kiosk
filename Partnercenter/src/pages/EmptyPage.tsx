import React from 'react';

interface EmptyPageProps {
  title: string;
}

export default function EmptyPage({ title }: EmptyPageProps) {
  return (
    <div className="flex-1 p-8 flex flex-col justify-center items-center bg-[#F9FAFB] min-h-screen">
      <div className="bg-white p-12 rounded-2xl shadow-sm text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">{title}</h1>
        <p className="text-xl text-gray-500">이 페이지는 현재 개발 중입니다 🛠️</p>
      </div>
    </div>
  );
}
