import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function PassRateChart({ data }) {
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="4 4" stroke="rgba(16, 36, 29, 0.12)" />
          <XAxis dataKey="name" stroke="#30473f" />
          <YAxis domain={[0, 1]} stroke="#30473f" />
          <Tooltip />
          <Line type="monotone" dataKey="passRate" stroke="#0f766e" strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
