import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy - Spotfinder",
  description: "Spotfinder Privacy Policy",
};

export default function PrivacyPolicyEnPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-4 py-12">
        {/* Language Switcher */}
        <div className="flex gap-2 mb-8 text-sm">
          <Link href="/privacy" className="text-gray-500 hover:text-gray-900">
            한국어
          </Link>
          <span className="text-gray-300">|</span>
          <span className="font-semibold text-gray-900">English</span>
          <span className="text-gray-300">|</span>
          <Link href="/privacy/ja" className="text-gray-500 hover:text-gray-900">
            日本語
          </Link>
        </div>

        <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>

        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-8">
            Spotfinder ("Service") values your privacy and complies with applicable data protection laws.
          </p>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">1. Information We Collect</h2>
            <p className="text-gray-700 mb-2">We collect the following personal information:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>Email address (when signing in via OAuth)</li>
              <li>Profile information (name, profile picture - from OAuth provider)</li>
              <li>Location data (when using map services, optional)</li>
              <li>Device identifiers (for push notification services)</li>
              <li>Service usage records and access logs</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">2. How We Use Your Information</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>Providing services and managing accounts</li>
              <li>Personalized popup store recommendations</li>
              <li>Sending push notifications (new popup stores, events)</li>
              <li>Service improvement and analytics</li>
              <li>Customer support</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">3. Data Retention</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>Data is deleted immediately upon account deletion</li>
              <li>Certain data may be retained as required by law</li>
              <li>Access logs: 3 months (as required by applicable regulations)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">4. Sharing Your Information</h2>
            <p className="text-gray-700">
              We do not share your personal information with third parties without your consent,
              except in the following cases:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
              <li>When required by law or legal process</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">5. Data Security</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>Encryption of personal data</li>
              <li>Security systems to protect against unauthorized access</li>
              <li>Access controls for personal information</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">6. Your Rights</h2>
            <p className="text-gray-700 mb-2">You have the right to:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>Access your personal information</li>
              <li>Correct your personal information</li>
              <li>Delete your personal information</li>
              <li>Request suspension of data processing</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">7. Cookies</h2>
            <p className="text-gray-700">
              We use cookies to improve your experience. You can disable cookies in your browser settings,
              but this may limit some features of the service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">8. Contact Us</h2>
            <p className="text-gray-700">
              For privacy-related inquiries, please contact us at:
            </p>
            <p className="text-gray-700 mt-2">
              Email: <a href="mailto:privacy@wigtn.com" className="text-blue-600 hover:underline">privacy@wigtn.com</a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">9. Changes to This Policy</h2>
            <p className="text-gray-700">
              This privacy policy is effective as of the date below. We will notify you of any changes
              at least 7 days before they take effect through notices on our service.
            </p>
          </section>

          <div className="border-t pt-6 mt-8">
            <p className="text-sm text-gray-500">Effective Date: January 31, 2026</p>
            <p className="text-sm text-gray-500">Last Updated: January 31, 2026</p>
          </div>
        </div>

        <div className="mt-12">
          <Link href="/" className="text-blue-600 hover:underline">
            &larr; Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
