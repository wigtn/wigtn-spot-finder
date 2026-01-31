import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "개인정보처리방침 - Spotfinder",
  description: "Spotfinder 개인정보처리방침",
};

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-4 py-12">
        {/* Language Switcher */}
        <div className="flex gap-2 mb-8 text-sm">
          <span className="font-semibold text-gray-900">한국어</span>
          <span className="text-gray-300">|</span>
          <Link href="/privacy/en" className="text-gray-500 hover:text-gray-900">
            English
          </Link>
          <span className="text-gray-300">|</span>
          <Link href="/privacy/ja" className="text-gray-500 hover:text-gray-900">
            日本語
          </Link>
        </div>

        <h1 className="text-3xl font-bold mb-8">개인정보처리방침</h1>

        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-8">
            Spotfinder(이하 "서비스")는 이용자의 개인정보를 중요시하며, 개인정보보호법을 준수합니다.
          </p>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">1. 수집하는 개인정보</h2>
            <p className="text-gray-700 mb-2">서비스는 다음과 같은 개인정보를 수집합니다:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>이메일 주소 (OAuth 로그인 시)</li>
              <li>프로필 정보 (이름, 프로필 사진 - OAuth 제공자로부터)</li>
              <li>위치 정보 (지도 서비스 이용 시, 선택적)</li>
              <li>기기 식별자 (푸시 알림 서비스)</li>
              <li>서비스 이용 기록 및 접속 로그</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">2. 개인정보 이용 목적</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>서비스 제공 및 회원 관리</li>
              <li>맞춤형 팝업스토어 추천</li>
              <li>푸시 알림 발송 (새로운 팝업스토어, 이벤트 안내)</li>
              <li>서비스 개선 및 통계 분석</li>
              <li>고객 문의 응대</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">3. 개인정보 보유 및 이용 기간</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>회원 탈퇴 시 즉시 삭제</li>
              <li>단, 관련 법령에 따라 보관이 필요한 경우 해당 기간 동안 보관</li>
              <li>접속 로그: 3개월 (통신비밀보호법)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">4. 개인정보의 제3자 제공</h2>
            <p className="text-gray-700">
              서비스는 이용자의 동의 없이 개인정보를 제3자에게 제공하지 않습니다.
              단, 다음의 경우는 예외로 합니다:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
              <li>법령에 의거하거나 수사 목적으로 법령에 정해진 절차와 방법에 따른 요청이 있는 경우</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">5. 개인정보의 안전성 확보 조치</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>개인정보 암호화</li>
              <li>해킹 등에 대비한 보안 시스템 구축</li>
              <li>개인정보 접근 제한</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">6. 이용자의 권리</h2>
            <p className="text-gray-700 mb-2">이용자는 다음과 같은 권리를 행사할 수 있습니다:</p>
            <ul className="list-disc pl-6 text-gray-700 space-y-1">
              <li>개인정보 열람 요청</li>
              <li>개인정보 정정 요청</li>
              <li>개인정보 삭제 요청</li>
              <li>개인정보 처리 정지 요청</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">7. 쿠키 사용</h2>
            <p className="text-gray-700">
              서비스는 이용자 경험 개선을 위해 쿠키를 사용합니다.
              브라우저 설정을 통해 쿠키 저장을 거부할 수 있으나, 일부 서비스 이용에 제한이 있을 수 있습니다.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">8. 개인정보 보호책임자</h2>
            <p className="text-gray-700">
              개인정보 관련 문의는 아래로 연락해 주시기 바랍니다.
            </p>
            <p className="text-gray-700 mt-2">
              이메일: <a href="mailto:privacy@wigtn.com" className="text-blue-600 hover:underline">privacy@wigtn.com</a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">9. 개인정보처리방침 변경</h2>
            <p className="text-gray-700">
              이 개인정보처리방침은 시행일로부터 적용되며, 법령 및 방침에 따른 변경 내용의 추가, 삭제 및 정정이 있는 경우에는
              변경사항의 시행 7일 전부터 공지사항을 통하여 고지할 것입니다.
            </p>
          </section>

          <div className="border-t pt-6 mt-8">
            <p className="text-sm text-gray-500">시행일: 2026년 1월 31일</p>
            <p className="text-sm text-gray-500">최종 수정일: 2026년 1월 31일</p>
          </div>
        </div>

        <div className="mt-12">
          <Link href="/" className="text-blue-600 hover:underline">
            &larr; 홈으로 돌아가기
          </Link>
        </div>
      </div>
    </div>
  );
}
