import type { ChatPopupCard } from "@/types";

const POPUP_CARDS_START = "<<<POPUP_CARDS>>>";
const POPUP_CARDS_END = "<<<END_POPUP_CARDS>>>";

export interface ParsedMessageContent {
  textBefore: string;
  textAfter: string;
  popupCards: ChatPopupCard[] | null;
}

/**
 * Parse message content to extract popup card data and text
 */
export function parseMessageContent(content: string): ParsedMessageContent {
  const startIndex = content.indexOf(POPUP_CARDS_START);
  const endIndex = content.indexOf(POPUP_CARDS_END);

  // No popup cards block found
  if (startIndex === -1 || endIndex === -1 || startIndex >= endIndex) {
    return {
      textBefore: content,
      textAfter: "",
      popupCards: null,
    };
  }

  const textBefore = content.substring(0, startIndex).trim();
  const textAfter = content.substring(endIndex + POPUP_CARDS_END.length).trim();
  const jsonString = content.substring(startIndex + POPUP_CARDS_START.length, endIndex).trim();

  let popupCards: ChatPopupCard[] | null = null;

  try {
    const parsed = JSON.parse(jsonString);
    if (Array.isArray(parsed)) {
      popupCards = parsed as ChatPopupCard[];
    }
  } catch (e) {
    console.error("Failed to parse popup cards JSON:", e);
  }

  return {
    textBefore,
    textAfter,
    popupCards,
  };
}
