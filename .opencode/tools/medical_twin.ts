import { tool } from "@opencode-ai/plugin"
import path from "node:path"

async function runBridge(
  args: Record<string, unknown>,
  context: { worktree: string },
): Promise<string> {
  const runner = path.join(context.worktree, ".opencode", "tools", "medical_twin_runner.py")
  const payload = Buffer.from(JSON.stringify(args), "utf8").toString("base64")
  const child = Bun.spawn(
    ["python3", runner, "--payload-base64", payload, "--worktree", context.worktree],
    {
      cwd: context.worktree,
      stdout: "pipe",
      stderr: "pipe",
    },
  )
  const [stdout, stderr, exitCode] = await Promise.all([
    new Response(child.stdout).text(),
    new Response(child.stderr).text(),
    child.exited,
  ])
  if (exitCode !== 0) {
    throw new Error((stdout || stderr || `bridge encerrou com código ${exitCode}`).trim())
  }
  return stdout.trim()
}

const commonArgs = {
  case_file: tool.schema.string().describe("Caminho relativo do JSON sintético no projeto"),
  horizon: tool.schema.number().optional().describe("Estados temporais, entre 2 e 12"),
  seed: tool.schema.number().optional().describe("Seed inteira para reprodução"),
  output_file: tool.schema.string().optional().describe("Caminho relativo opcional da saída"),
}

export const validate = tool({
  description: "Valida um caso médico sintético sem executar simulação.",
  args: { case_file: commonArgs.case_file },
  async execute(args, context) {
    return runBridge({ operation: "validate", case_file: args.case_file }, context)
  },
})

export const simulate = tool({
  description: "Executa localmente um gêmeo digital exclusivamente sintético com revisão Reversa.",
  args: commonArgs,
  async execute(args, context) {
    return runBridge({ operation: "simulate", adapter: "deterministic", ...args }, context)
  },
})

export const mirofish = tool({
  description: "Executa simulação sintética pelo bridge MiroFish configurado pelo operador.",
  args: commonArgs,
  async execute(args, context) {
    return runBridge({ operation: "simulate", adapter: "mirofish", ...args }, context)
  },
})
