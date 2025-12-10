import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
import openai
import requests
import json
import os
import sys
import google.generativeai as genai
sys.path.append("/Users/kyleloboprabhu/Library/Python/3.9/lib/python/site-packages")


# === Nano Agent ===
class NanoAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.endpoint = "https://api.openai.com/v1/responses"

    def call_llm(self, input_text):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": "gpt-5-nano",
            "input": input_text,
            "store": True
        }

        response = requests.post(self.endpoint, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")

        data = response.json()

        for item in data:
            if item.get("type") == "message":
                for block in item.get("content", []):
                    if block.get("type") == "output_text":
                        return block.get("text", "No output text found.")
        return "No valid output found."

    def run(self, goal, command, log_callback):
        log_callback(f"\n🧠 Starting Nano agent with goal: {goal}")
        log_callback(f"\n💻 Run Command: {command}")

        try:
            prompt = f"My goal is: {goal}. Please help me run: {command}"
            reply_text = self.call_llm(prompt)

            log_callback(f"\n🤖 LLM Response:\n{reply_text}")
            log_callback("\n✅ Goal achieved by Nano agent.")

            filename = "generated_script.py"
            with open(filename, "w") as f:
                f.write(reply_text)
            log_callback(f"\n💾 Saved output to file: {filename}")

        except Exception as e:
            log_callback(f"\n❌ Error: {str(e)}")


# === Gemini Agent ===
class GeminiAgent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def call_llm(self, messages):
        prompt = "\n".join([msg["content"] for msg in messages if msg["role"] == "user"])
        response = self.model.generate_content(prompt)
        return response.text

    def run(self, goal, command, log_callback):
        log_callback(f"\n🧠 Starting Gemini agent with goal: {goal}")
        log_callback(f"\n💻 Run Command: {command}")

        messages = [
            {"role": "user", "content": f"My goal is: {goal}. Please help me run: {command}"}
        ]

        try:
            reply = self.call_llm(messages)
            log_callback(f"\n🤖 LLM Response:\n{reply}")
            log_callback("\n✅ Goal achieved by Gemini agent.")
        except Exception as e:
            log_callback(f"\n❌ Error: {str(e)}")


# === LangGraph Agent ===
class LangGraphAgent:
    def __init__(self, llm_backend="ChatGPT", api_key="", azure_config=None):
        self.llm_backend = llm_backend
        self.api_key = api_key
        self.azure_config = azure_config or {}

        if llm_backend == "ChatGPT":
            self.client = openai.OpenAI(api_key=api_key)
        elif llm_backend == "Copilot":
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=azure_config.get("api_version", "2023-07-01-preview"),
                azure_endpoint=azure_config.get("api_base", "")
            )

    def call_llm(self, messages):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo" if self.llm_backend == "ChatGPT" else self.azure_config.get("deployment_name", "gpt-4"),
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content

    def run(self, goal, command, log_callback):
        log_callback(f"\n🧠 Starting LangGraph agent with goal: {goal}")
        log_callback(f"\n💻 Run Command: {command}")

        messages = [
            {"role": "system", "content": "You are a helpful agent."},
            {"role": "user", "content": f"My goal is: {goal}. Please help me run: {command}"}
        ]

        try:
            reply = self.call_llm(messages)
            log_callback(f"\n🤖 LLM Response:\n{reply}")
            log_callback("\n✅ Goal achieved by LangGraph agent.")
        except Exception as e:
            log_callback(f"\n❌ Error: {str(e)}")


# === GUI ===
class AgentGUI:
    def __init__(self, root, agent):
        self.agent = agent
        root.title("LangGraph Agent GUI")

        tk.Label(root, text="Goal:").pack(pady=(10, 0))
        self.goal_entry = tk.Entry(root, width=60)
        self.goal_entry.pack(pady=5)

        tk.Label(root, text="Run Command:").pack(pady=(10, 0))
        self.command_entry = tk.Entry(root, width=60)
        self.command_entry.pack(pady=5)

        tk.Label(root, text="LLM Backend:").pack(pady=(10, 0))
        self.llm_selector = ttk.Combobox(root, values=["ChatGPT", "Copilot", "Gemini", "Nano"])
        self.llm_selector.current(0)
        self.llm_selector.pack(pady=5)

        tk.Label(root, text="API Key:").pack(pady=(10, 0))
        self.api_key_entry = tk.Entry(root, width=60, show="*")
        self.api_key_entry.pack(pady=5)

        self.run_button = tk.Button(root, text="Run Agent", command=self.run_agent_threaded)
        self.run_button.pack(pady=10)

        self.save_button = tk.Button(root, text="Save Output to File", command=self.save_output_to_file)
        self.save_button.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, width=80, height=20)
        self.log_area.pack(pady=10)

    def log(self, message):
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END)

    def run_agent_threaded(self):
        goal = self.goal_entry.get()
        command = self.command_entry.get()
        llm_backend = self.llm_selector.get()
        api_key = self.api_key_entry.get()

        azure_config = {
            "api_base": "https://your-resource-name.openai.azure.com/",
            "api_version": "2023-07-01-preview",
            "deployment_name": "gpt-4"
        } if llm_backend == "Copilot" else None

        if llm_backend == "Gemini":
            self.agent = GeminiAgent(api_key)
        elif llm_backend == "Nano":
            self.agent = NanoAgent(api_key)
        else:
            self.agent = LangGraphAgent(llm_backend, api_key, azure_config)

        self.log(f"\n🎯 Goal: {goal}")
        self.log(f"\n💬 Command: {command}")
        self.log(f"\n⚙️ Using LLM: {llm_backend}")

        threading.Thread(target=self.agent.run, args=(goal, command, self.log)).start()

    def save_output_to_file(self):
        import re
        content = self.log_area.get("1.0", tk.END)
        match = re.search(r"🤖 LLM Response:\n(.*?)\n✅", content, re.DOTALL)
        if match:
            output_text = match.group(1).strip()
        else:
            self.log("\n⚠️ No LLM response found to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if file_path:
            with open(file_path, "w") as f:
                f.write(output_text)
            self.log(f"\n💾 Saved output to: {file_path}")
        else:
            self.log("\n❌ Save cancelled.")


# === Main ===
if __name__ == "__main__":
    root = tk.Tk()
    gui = AgentGUI(root, None)
    root.mainloop()
