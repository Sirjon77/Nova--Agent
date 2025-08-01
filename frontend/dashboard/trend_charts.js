
import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'

export default function TrendInsightsPanel() {
  const [data, setData] = useState([])

  useEffect(() => {
    fetch('/matched_trends_to_rpm.json')
      .then(res => res.json())
      .then(setData)
  }, [])

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-2">Trend Matching: RPM vs Segment</h2>
      <BarChart width={500} height={300} data={data}>
        <XAxis dataKey="trend_segment" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="rpm" fill="#8884d8" />
      </BarChart>
    </div>
  )
}
