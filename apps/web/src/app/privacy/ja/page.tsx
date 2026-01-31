import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "プライバシーポリシー - Spotfinder",
  description: "Spotfinder プライバシーポリシー",
};

export default function PrivacyPolicyJaPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-4 py-12">
        {/* Language Switcher */}
        <div className="flex gap-2 mb-8 text-sm">
          <Link href="/privacy" className="text-gray-500 hover:text-gray-900">
            한국어
          </Link>
          <span className="text-gray-300">|</span>
          <Link href="/privacy/en" className="text-gray-500 hover:text-gray-900">
            English
          </Link>
          <span className="text-gray-300">|</span>
          <span className="font-semibold text-gray-900">日本語</span>
        </div>

        <h1 className="text-3xl font-bold mb-8">プライバシーポリシー</h1>

        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-8">
            Spotfinder（以下「本サービス」）は、お客様の個人情報を大切に扱い、関連法令を遵守します。
          </p>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">1. 収集する個人情報</h2>
            <p className="text-gray-700 mb-2">本サービスは以下の個人情報を収集します：</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>メールアドレス（OAuthログイン時）</li>
              <li>プロフィール情報（氏名、プロフィール写真 - OAuthプロバイダーから取得）</li>
              <li>位置情報（地図サービス利用時、任意）</li>
              <li>デバイス識別子（プッシュ通知サービス）</li>
              <li>サービス利用記録およびアクセスログ</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">2. 個人情報の利用目的</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>サービス提供および会員管理</li>
              <li>パーソナライズされたポップアップストアのおすすめ</li>
              <li>プッシュ通知の送信（新しいポップアップストア、イベント案内）</li>
              <li>サービス改善および統計分析</li>
              <li>カスタマーサポート</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">3. 個人情報の保持期間</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>アカウント削除時に即時削除</li>
              <li>ただし、法令で保管が必要な場合は該当期間保管</li>
              <li>アクセスログ：3ヶ月（関連法規に基づく）</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">4. 個人情報の第三者提供</h2>
            <p className="text-gray-700">
              本サービスは、お客様の同意なく個人情報を第三者に提供しません。
              ただし、以下の場合は例外とします：
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
              <li>法令に基づく場合、または法的手続きによる要請がある場合</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">5. 個人情報の安全管理措置</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>個人情報の暗号化</li>
              <li>不正アクセス防止のためのセキュリティシステム</li>
              <li>個人情報へのアクセス制限</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">6. お客様の権利</h2>
            <p className="text-gray-700 mb-2">お客様は以下の権利を行使できます：</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>個人情報の開示請求</li>
              <li>個人情報の訂正請求</li>
              <li>個人情報の削除請求</li>
              <li>個人情報処理の停止請求</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">7. Cookieの使用</h2>
            <p className="text-gray-700">
              本サービスは、ユーザー体験向上のためCookieを使用します。
              ブラウザ設定でCookieを無効にすることができますが、一部機能が制限される場合があります。
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">8. お問い合わせ</h2>
            <p className="text-gray-700">
              プライバシーに関するお問い合わせは、以下までご連絡ください。
            </p>
            <p className="text-gray-700 mt-2">
              メール: <a href="mailto:privacy@wigtn.com" className="text-blue-600 hover:underline">privacy@wigtn.com</a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">9. ポリシーの変更</h2>
            <p className="text-gray-700">
              このプライバシーポリシーは以下の日付から適用されます。
              変更がある場合は、変更の7日前までにサービス上でお知らせします。
            </p>
          </section>

          <div className="border-t pt-6 mt-8">
            <p className="text-sm text-gray-500">施行日: 2026年1月31日</p>
            <p className="text-sm text-gray-500">最終更新日: 2026年1月31日</p>
          </div>
        </div>

        <div className="mt-12">
          <Link href="/" className="text-blue-600 hover:underline">
            &larr; ホームに戻る
          </Link>
        </div>
      </div>
    </div>
  );
}
