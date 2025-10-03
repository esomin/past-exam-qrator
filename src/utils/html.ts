/**
 * HTML p 태그를 제거하고 텍스트를 정리합니다
 */
export const stripPTag = (text: string | null | undefined): string => {
  return (text || "").replace(/<\/?p[^>]*>/gi, "").trim();
};

/**
 * 모든 HTML 태그를 제거합니다
 */
export const stripAllHtml = (text: string | null | undefined): string => {
  return (text || "").replace(/<[^>]*>/g, "").trim();
};