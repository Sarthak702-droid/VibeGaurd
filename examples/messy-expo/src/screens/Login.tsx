import React, { useState } from "react";
import { Button, Text, TextInput, View } from "react-native";
import { loginWithPassword } from "../services/auth";

export default function LoginScreen() {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  async function onLogin() {
    await loginWithPassword(phone, password);
  }

  return (
    <View>
      <Text>Login</Text>
      <TextInput value={phone} onChangeText={setPhone} placeholder="Phone" />
      <TextInput value={password} onChangeText={setPassword} placeholder="Password" secureTextEntry />
      <Button title="Login" onPress={onLogin} />
    </View>
  );
}

