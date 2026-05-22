import { Settings, KeyRound, Bell, Users, Sparkles } from "lucide-react";

const PLANNED = [
  {
    icon: KeyRound,
    title: "API Keys",
    desc: "Manage your Anthropic and OpenAI keys, set token budgets per analysis.",
  },
  {
    icon: Bell,
    title: "Notifications",
    desc: "Email and webhook alerts when analysis completes or critical debt is found.",
  },
  {
    icon: Users,
    title: "Team & Access",
    desc: "Invite teammates, share projects, and manage role-based permissions.",
  },
];

export default function SettingsPage() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center space-y-10 animate-[fade-in_0.5s_ease-out]">
      <div className="text-center space-y-4">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-muted ring-1 ring-border mb-6">
          <Settings className="h-10 w-10 text-muted-foreground" />
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-xs font-medium text-muted-foreground">
          <Sparkles className="h-3 w-3" />
          Coming Soon
        </div>
        <h1 className="text-4xl font-bold tracking-tight">Settings</h1>
        <p className="max-w-md text-muted-foreground text-sm leading-relaxed">
          Configure your account, API keys, and notification preferences.
          Full settings panel launching soon.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3 w-full max-w-2xl">
        {PLANNED.map((f) => (
          <div key={f.title} className="glass rounded-xl p-5 space-y-2 opacity-75">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
              <f.icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-sm font-semibold">{f.title}</p>
            <p className="text-xs text-muted-foreground leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
