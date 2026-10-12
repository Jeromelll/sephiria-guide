import { handleAuth } from "../../_shared/site-auth/handler.js";

export async function onRequest(context) {
  const response = await handleAuth(context.request, context.env);
  return response ?? context.next();
}
