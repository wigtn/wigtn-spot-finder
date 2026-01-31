import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "이용약관 - Spotfinder",
  description: "Spotfinder 서비스 이용약관",
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-8">서비스 이용약관</h1>

        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-8">
            본 약관은 Spotfinder(이하 "서비스")의 이용에 관한 조건 및 절차, 기타 필요한 사항을 규정합니다.
          </p>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제1조 (목적)</h2>
            <p className="text-gray-700">
              본 약관은 서비스가 제공하는 팝업스토어 정보 및 AI 추천 서비스(이하 "서비스")의 이용과 관련하여
              서비스와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제2조 (정의)</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>"서비스"란 팝업스토어 정보 제공, AI 기반 추천, 지도 서비스 등을 말합니다.</li>
              <li>"이용자"란 본 약관에 따라 서비스를 이용하는 회원 및 비회원을 말합니다.</li>
              <li>"회원"이란 서비스에 가입하여 계정을 생성한 자를 말합니다.</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제3조 (약관의 효력)</h2>
            <p className="text-gray-700">
              본 약관은 서비스를 이용하고자 하는 모든 이용자에게 적용됩니다.
              서비스 이용 시 본 약관에 동의한 것으로 간주됩니다.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제4조 (서비스의 제공)</h2>
            <p className="text-gray-700 mb-2">서비스는 다음과 같은 기능을 제공합니다:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>성수동 팝업스토어 정보 제공</li>
              <li>AI 기반 맞춤 추천</li>
              <li>지도 기반 위치 안내</li>
              <li>푸시 알림 서비스</li>
              <li>다국어 지원 (한국어, 영어, 일본어)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제5조 (이용자의 의무)</h2>
            <p className="text-gray-700 mb-2">이용자는 다음 행위를 하여서는 안 됩니다:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>타인의 정보를 도용하는 행위</li>
              <li>서비스의 운영을 방해하는 행위</li>
              <li>서비스 정보를 무단으로 수집, 저장, 공개하는 행위</li>
              <li>서비스를 영리 목적으로 이용하는 행위</li>
              <li>기타 법령 또는 본 약관에 위배되는 행위</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제6조 (면책조항)</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>서비스는 팝업스토어 정보의 정확성을 보장하지 않으며, 정보의 오류로 인한 손해에 대해 책임지지 않습니다.</li>
              <li>팝업스토어의 운영 시간, 위치, 기간 등은 실제와 다를 수 있습니다.</li>
              <li>AI 추천은 참고용이며, 최종 결정은 이용자의 책임입니다.</li>
              <li>서비스는 천재지변, 시스템 장애 등 불가항력으로 인한 서비스 중단에 대해 책임지지 않습니다.</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제7조 (지적재산권)</h2>
            <p className="text-gray-700">
              서비스에 포함된 모든 콘텐츠(텍스트, 이미지, 소프트웨어 등)에 대한 저작권 및 지적재산권은
              서비스 또는 해당 권리자에게 귀속됩니다.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제8조 (서비스 변경 및 중단)</h2>
            <p className="text-gray-700">
              서비스는 운영상, 기술상의 필요에 따라 서비스의 전부 또는 일부를 변경하거나 중단할 수 있습니다.
              이 경우 사전에 공지합니다.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제9조 (약관의 변경)</h2>
            <p className="text-gray-700">
              서비스는 필요한 경우 본 약관을 변경할 수 있으며, 변경된 약관은 서비스 내 공지 후 효력이 발생합니다.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">제10조 (준거법 및 관할)</h2>
            <p className="text-gray-700">
              본 약관의 해석 및 적용에 관하여는 대한민국 법률을 준거법으로 합니다.
            </p>
          </section>

          <div className="border-t pt-6 mt-8">
            <p className="text-sm text-gray-500">시행일: 2026년 1월 31일</p>
          </div>
        </div>

        <div className="mt-12 flex gap-4">
          <Link href="/" className="text-blue-600 hover:underline">
            &larr; 홈으로 돌아가기
          </Link>
          <Link href="/privacy" className="text-blue-600 hover:underline">
            개인정보처리방침
          </Link>
        </div>
      </div>
    </div>
  );
}
