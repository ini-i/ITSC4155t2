import AsyncStorage from "@react-native-async-storage/async-storage"; //adding for testing for questions
import { router } from "expo-router";
import { useState } from "react";
import {
  Alert,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { API_BASE_URL } from "../lib/api";

export default function ChildLoginScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleChildAuth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/student/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        Alert.alert("Login Failed", data.detail || "Incorrect login");
        return;
      }
      await AsyncStorage.setItem("token", data.access_token);
      await AsyncStorage.setItem("username", data.username);
      await AsyncStorage.setItem("user_id", String(data.id));
      console.log("LOGIN SUCCESS:", data);

      //adding for testing for questions
      //await AsyncStorage.setItem("token", data.access_token);
      //await AsyncStorage.setItem("user_id", String(data.id));

      Alert.alert("Welcome!", `Hi ${data.username}!`);
      router.push("/ActivityMap");
    } catch (error) {
      Alert.alert("Error", "Could not connect to server");
      console.log(error);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}> Student Login</Text>
        <Text style={styles.subtitle}>Ready?</Text>

        {/* Inputs */}
        <TextInput
          style={styles.input}
          placeholder="Name"
          placeholderTextColor="#7a7a7a"
          value={username}
          onChangeText={setUsername}
        />

        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#7a7a7a"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        {/* Submit */}
        <TouchableOpacity style={styles.submitBtn} onPress={handleChildAuth}>
          <Text style={styles.submitText}>Start</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.backText}>Back</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#5cbbcc",
    justifyContent: "center",
    padding: 24,
  },

  card: {
    backgroundColor: "#FFF9F3",
    borderRadius: 28,
    padding: 24,
    elevation: 6,
  },

  title: {
    fontSize: 30,
    fontWeight: "900",
    color: "#355c9a",
    textAlign: "center",
    marginBottom: 8,
  },

  subtitle: {
    textAlign: "center",
    color: "#355c9a",
    fontWeight: "700",
    marginBottom: 20,
  },
  input: {
    backgroundColor: "#fff",
    borderRadius: 18,
    paddingHorizontal: 18,
    paddingVertical: 14,
    marginBottom: 14,
    fontSize: 16,
  },
  submitBtn: {
    backgroundColor: "#67d9e8",
    paddingVertical: 16,
    borderRadius: 24,
    alignItems: "center",
    marginTop: 10,
  },
  submitText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "900",
  },
  backText: {
    textAlign: "center",
    marginTop: 18,
    color: "#355c9a",
    fontWeight: "700",
  },
});
