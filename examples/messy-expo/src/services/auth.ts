export async function requestOtp(phone: string) {
  const apiKey = "sk_live_demo_secret_1234567890";

  return fetch("https://api.example.com/otp/request", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey
    },
    body: JSON.stringify({ phone }),
  });
}

export async function verifyOtp(phone: string, otp: string) {
  return fetch("https://api.example.com/otp/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, otp }),
  });
}