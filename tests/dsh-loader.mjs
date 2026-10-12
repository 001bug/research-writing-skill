/** Offline integration test against the installed DSH provider and registry. */
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtemp, mkdir, realpath, readdir, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'
import { parseArgs } from 'node:util'

const { values } = parseArgs({ options: {
  'dsh-root': { type: 'string' }, source: { type: 'string' }, python: { type: 'string', default: 'python3' },
  'installed-home': { type: 'string' },
} })
if (!values['dsh-root'] || !values.source) throw new Error('--dsh-root and --source are required')
const dsh = resolve(values['dsh-root'])
const source = resolve(values.source)
const names = new Set((await readdir(join(source, 'skills'), { withFileTypes: true })).filter(d => d.isDirectory()).map(d => d.name))
assert.equal(names.size, 19)
const moduleAt = rel => import(pathToFileURL(join(dsh, rel)).href)
const requireDsh = createRequire(join(dsh, 'packages/skill/skill-filesystem/package.json'))
const { Context } = await import(pathToFileURL(requireDsh.resolve('@deepseek-ai/cordis')).href)
const { default: SkillRegistry } = await moduleAt('packages/skill/skill/src/index.ts')
const SkillFileSystem = await moduleAt('packages/skill/skill-filesystem/src/index.ts')
const temp = await mkdtemp(join(tmpdir(), 'dsh-论文 空格-'))
let ctx
try {
  const home = values['installed-home'] ? resolve(values['installed-home']) : join(temp, '用户 配置')
  const workspaces = [join(temp, '论文 A'), join(temp, '论文 B')]
  for (const workspace of workspaces) await mkdir(join(workspace, '.git'), { recursive: true })
  if (!values['installed-home']) {
    const install = spawnSync(values.python, [join(source, 'scripts/install_dsh.py'), '--root', source, '--dsh-home', home], { encoding: 'utf8' })
    assert.equal(install.status, 0, install.stderr)
  }
  ctx = new Context()
  await ctx.plugin(SkillRegistry)
  await ctx.plugin(SkillFileSystem, {
    dshHome: home, agentsHome: join(temp, 'empty-agents'), bundledSkillDir: join(temp, 'empty-bundled'), watch: false,
  })
  for (const cwd of workspaces) {
    const skills = (await ctx.skills.list({ cwd })).filter(s => names.has(s.name))
    assert.equal(skills.length, 19)
    assert.equal(new Set(skills.map(s => s.name)).size, 19)
    for (const summary of skills) {
      const loaded = await ctx.skills.get(summary.name, { cwd })
      assert.ok(loaded.content.includes('## DSH 运行约定'), summary.name)
      assert.equal(loaded.resourceBase.kind, 'directory')
      assert.equal(resolve(await realpath(loaded.resourceBase.path), '../..'), source)
    }
  }
  // Exercise the real registry's project-over-user winner selection.
  const local = join(workspaces[0], '.dsh/skills/writing-humanities')
  await mkdir(local, { recursive: true })
  await writeFile(join(local, 'SKILL.md'), '---\nname: writing-humanities\ndescription: Project override fixture\n---\nProject override body.\n')
  // With watch disabled, use a fresh registry after changing the filesystem.
  await ctx.fiber.dispose()
  ctx = new Context()
  await ctx.plugin(SkillRegistry)
  await ctx.plugin(SkillFileSystem, {
    dshHome: home, agentsHome: join(temp, 'empty-agents'), bundledSkillDir: join(temp, 'empty-bundled'), watch: false,
  })
  const overridden = await ctx.skills.get('writing-humanities', { cwd: workspaces[0] })
  assert.ok(overridden.content.includes('Project override body.'))
  const global = await ctx.skills.get('writing-humanities', { cwd: workspaces[1] })
  assert.ok(global.content.includes('## DSH 运行约定'))
  console.log(`PASS: actual DSH loader discovers and loads 19 skills in 2 workspaces; resource roots and project precedence verified. ${values['installed-home'] ? 'Existing user installation checked read-only.' : 'Isolated installation checked.'} No model calls.`)
} finally {
  if (ctx) await ctx.fiber.dispose()
  await rm(temp, { recursive: true, force: true })
}
