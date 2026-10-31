import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          Account configuration, security credentials, and system observability parameters.
        </p>
      </div>

      <div className="max-w-2xl space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Crawler Security Policy</CardTitle>
            <CardDescription>Target domain boundaries and SSRF prevention constraints</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 space-y-2">
            <p>Domain ownership verification: Required via DNS TXT record.</p>
            <p>Private IP blocking: RFC 1918, loopback, and metadata endpoints strictly blocked.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
