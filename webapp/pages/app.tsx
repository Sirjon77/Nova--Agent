export default async function Dashboard() {
  // Example React 19 server action
  async function getData() {
    "use server";
    return { message: "Hello from server actions!" };
  }
  const data = await getData();
  return <div className="p-8 text-xl">{data.message}</div>;
}
