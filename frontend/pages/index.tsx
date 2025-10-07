import { useState, useEffect } from 'react'
import { GitBranch, GitCommit, GitPullRequest, Play, FileText, Activity } from 'lucide-react'

interface ApiResponse {
  status: string
  result?: {
    content?: string
    [key: string]: any
  }
  error?: string
}

export default function Home() {
  const [loading, setLoading] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, ApiResponse>>({})
  const [repo, setRepo] = useState('benghita/PropertyValuation')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const callApi = async (endpoint: string, data: any, agentName: string) => {
    setLoading(agentName)
    try {
      console.log('Calling API:', `http://localhost:8000/api${endpoint}`, { ...data, repo })
      const response = await fetch(`http://localhost:8000/api${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data, repo })
      })
      const result = await response.json()
      console.log('API Response:', result)
      setResults(prev => ({ ...prev, [agentName]: result }))
    } catch (error) {
      console.error('API Error:', error)
      setResults(prev => ({ 
        ...prev, 
        [agentName]: { status: 'error', error: error instanceof Error ? error.message : 'Unknown error' } 
      }))
    } finally {
      setLoading(null)
    }
  }

  const agents = [
    {
      name: 'Repo Watcher',
      icon: <Activity className="w-5 h-5" />,
      description: 'Monitor repository for new commits and PRs',
      action: () => callApi('/watcher/scan', { prompt: 'Scan repository for new commits and PRs' }, 'Repo Watcher')
    },
    {
      name: 'Commit Agent',
      icon: <GitCommit className="w-5 h-5" />,
      description: 'Create and validate commits',
      action: () => callApi('/commit/create', {
        files: [{ path: 'configs/app.yaml', content: 'key: value', message: 'chore(config): sync' }],
        branch: 'auto/config-sync',
        create_pr: false
      }, 'Commit Agent')
    },
    {
      name: 'Branch Manager',
      icon: <GitBranch className="w-5 h-5" />,
      description: 'Manage automation branches',
      action: () => callApi('/branch/manage', { action: 'list' }, 'Branch Manager')
    },
    {
      name: 'Deployment Agent',
      icon: <Play className="w-5 h-5" />,
      description: 'Check and trigger deployments',
      action: () => callApi('/deployment/check', { check_since: '2025-10-06T00:00:00Z' }, 'Deployment Agent')
    },
    {
      name: 'Report Agent',
      icon: <FileText className="w-5 h-5" />,
      description: 'Generate repository reports',
      action: () => callApi('/report/generate', {
        since: '2025-10-01T00:00:00Z',
        sections: ['summary', 'compliance', 'recent_prs', 'open_issues']
      }, 'Report Agent')
    }
  ]

  if (!mounted) {
    return <div className="container">Loading...</div>
  }

  return (
    <div className="container">
      <header style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1 style={{ fontSize: '2.5em', marginBottom: '10px', color: 'var(--text-accent)' }}>GitOps Manager</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.2em' }}>AI-Powered GitOps Automation Dashboard</p>
      </header>

      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 style={{ color: 'var(--text-accent)', marginBottom: '12px' }}>Repository Configuration</h3>
        <input
          type="text"
          className="input"
          placeholder="Repository (owner/repo)"
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
        />
      </div>

      <div className="grid">
        {agents.map((agent) => (
          <div key={agent.name} className="agent-section">
            <div className="agent-title">
              {agent.icon} {agent.name}
            </div>
            <p className="agent-description">{agent.description}</p>
            
            <button
              className="button"
              onClick={agent.action}
              disabled={loading === agent.name}
            >
              {loading === agent.name ? 'Running...' : 'Execute'}
            </button>

            {results[agent.name] && (
              <div className="result">
                <div style={{ marginBottom: '8px', color: 'var(--text-accent)', fontSize: '12px', fontWeight: '600' }}>
                  Agent Response:
                </div>
                <pre style={{ margin: 0, fontSize: '11px', lineHeight: '1.3' }}>
                  {results[agent.name].result?.content || 
                   JSON.stringify(results[agent.name], null, 2)}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ color: 'var(--text-accent)', marginBottom: '12px' }}>System Status</h3>
        <p style={{ margin: '4px 0', fontSize: '13px' }}>Backend API: <span className="status-success">Connected</span></p>
        <p style={{ margin: '4px 0', fontSize: '13px' }}>Repository: <code style={{ background: 'var(--bg-tertiary)', padding: '2px 6px', borderRadius: '3px' }}>{repo}</code></p>
        <p style={{ margin: '4px 0', fontSize: '13px', color: 'var(--text-secondary)' }}>Last Updated: {new Date().toLocaleString()}</p>
      </div>
    </div>
  )
}
