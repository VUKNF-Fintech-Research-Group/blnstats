import LoginPage from "@/systemPages/PublicPages/Login/Login";
import React from 'react';
import { cookies } from 'next/headers'

export default async function Page() {
  async function deleteTokens() {
    "use server";
    let cookieStore = await cookies();
    cookieStore.delete("session");
  }
  return <LoginPage deleteTokens={deleteTokens}/>;
}