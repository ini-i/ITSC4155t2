const API_BASE_URL = "https://itsc4155t2.onrender.com";

// 🔐 LOGIN
export const loginStudent = async (username, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/student/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const text = await response.text();

    if (!response.ok) {
      throw new Error(text);
    }

    return JSON.parse(text);
  } catch (error) {
    console.log("LOGIN ERROR:", error);
    throw error;
  }
};
