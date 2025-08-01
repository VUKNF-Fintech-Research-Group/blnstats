import axios from 'axios';
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'


export default async function EndpointWrapper({
  children, 
  THIS_FILE_PATH, 
  REDIRECT_TO_LOGIN_URL, 
  BACKEND_CHECK_AUTH_URL,
  isSecured
}) {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get("session")?.value;



  let response;
  try {
    if (sessionCookie !== undefined) {
      response = await axios.get(BACKEND_CHECK_AUTH_URL, {
        headers: { Cookie: "session=" + sessionCookie }
      });
    }
  } catch (error) {
    console.log("[*] Error in " + THIS_FILE_PATH);
    console.log(error);
    redirect(REDIRECT_TO_LOGIN_URL);
  }



  try{
    if(isSecured){
      if(response !== undefined){
        if (response.status === 200){
          return children(response.data);
        }
      }
    }
    else{
      return children(response !== undefined ? response.data : undefined);
    }
  }
  catch(error){
    console.log("[*] Error in " + THIS_FILE_PATH);
    console.log(error);
    redirect(REDIRECT_TO_LOGIN_URL);
  }

  

  redirect(REDIRECT_TO_LOGIN_URL);
}
