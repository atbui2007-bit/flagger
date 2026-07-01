import { useQuery } from '@tanstack/react-query'

interface Commit {
  id: string
  sha: string
  short_sha: string
  message: string
  author_login: string
  agent_type: string
  attribution_confidence: string
  risk_level: string
  full_name: string
  pushed_at: string
  [key: string]: unknown
}

interface ActivityResponse {
  data: Commit[]
  next_cursor: string | null
  has_more: boolean
}

async function fetchRecentActivity(): Promise<ActivityResponse> {
  const response = await fetch('http://localhost:8000/activity/recent')

  if (!response.ok) {
    throw new Error(`Failed to load activity: ${response.status}`)
  }

  const data: unknown = await response.json()
  return data as ActivityResponse
}

function ActivityFeed() {
  const { data, error, isPending } = useQuery<ActivityResponse>({
    queryKey: ['activity', 'recent'],
    queryFn: fetchRecentActivity,
  })

  if (isPending) {
    return <p>Loading activity...</p>
  }

  if (error) {
    console.error(error)
    return <p>Failed to load activity</p>
  }

  return (
    <ul className="m-4 p-4">
      {data.data.map((commit) => (
        <li className="border-b py-3 last:border-b-0" key={commit.id}>
          <p className="mb-1">
            <span className="font-mono font-semibold">{commit.short_sha}</span>{' '}
            {commit.message}
          </p>
          <p className="text-sm text-gray-600">
            {commit.author_login} · {commit.agent_type} · {commit.risk_level}
          </p>
        </li>
      ))}
    </ul>
  )
}

export default ActivityFeed
