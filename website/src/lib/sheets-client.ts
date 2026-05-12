// Client-side Google Sheets API utilities — credentials read from localStorage

const SHEETS_BASE = 'https://sheets.googleapis.com/v4/spreadsheets';

export interface Appointment {
  id: string;
  patient_phone: string;
  patient_name: string;
  doctor_name: string;
  specialty: string;
  date_time: string;
  status: 'Scheduled' | 'Completed' | 'No-show' | 'Cancelled';
  lang: string;
  reminder_24h_sent: boolean;
  reminder_2h_sent: boolean;
  noshow_recovery_sent: boolean;
  feedback_sent: boolean;
  feedback_rating: number | null;
  google_review_sent: boolean;
  created_at: string;
}

export interface Patient {
  phone: string;
  lang: string;
  state: string;
  specialty: string;
  doctor_id: string;
  selected_date: string;
  selected_time: string;
  patient_name: string;
  conversation_json: string;
  last_visit: string;
  updated_at: string;
}

export interface ConversationMessage {
  role: 'patient' | 'bot';
  text: string;
  timestamp?: string;
}

export const LANG_FLAGS: Record<string, string> = {
  ar: '🇦🇪', en: '🇬🇧', hi: '🇮🇳', ur: '🇵🇰', tl: '🇵🇭', ml: '🇮🇳', fr: '🇫🇷',
};

export const LANG_NAMES: Record<string, string> = {
  ar: 'Arabic', en: 'English', hi: 'Hindi', ur: 'Urdu', tl: 'Filipino', ml: 'Malayalam', fr: 'French',
};

export function esc(s: unknown): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function starsHtml(rating: number | null): string {
  if (rating === null) return '—';
  const r = Math.max(1, Math.min(5, Math.round(rating)));
  return '★'.repeat(r) + '☆'.repeat(5 - r);
}

// Handles both ISO-8601 and the 'YYYY-MM-DD HH:mm' format documented in the README
export function parseDatetime(dt: string): Date {
  if (!dt) return new Date(NaN);
  return new Date(dt.replace(' ', 'T'));
}

async function fetchRange(apiKey: string, spreadsheetId: string, range: string): Promise<string[][]> {
  const url = `${SHEETS_BASE}/${encodeURIComponent(spreadsheetId)}/values/${encodeURIComponent(range)}?key=${encodeURIComponent(apiKey)}`;
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `Sheets API error ${res.status}`);
  }
  const data = await res.json();
  return data.values ?? [];
}

function rowToObject(headers: string[], row: string[]): Record<string, string> {
  const obj: Record<string, string> = {};
  headers.forEach((h, i) => { obj[h] = row[i] ?? ''; });
  return obj;
}

export async function fetchAppointments(apiKey: string, spreadsheetId: string): Promise<Appointment[]> {
  const rows = await fetchRange(apiKey, spreadsheetId, 'Appointments!A:O');
  if (rows.length < 2) return [];
  const [headers, ...data] = rows;
  return data
    .filter(row => row.length > 0 && row[0])
    .map(row => {
      const r = rowToObject(headers, row);
      const rating = parseInt(r.feedback_rating, 10);
      return {
        id: r.id,
        patient_phone: r.patient_phone,
        patient_name: r.patient_name,
        doctor_name: r.doctor_name,
        specialty: r.specialty,
        date_time: r.date_time,
        status: (r.status as Appointment['status']) || 'Scheduled',
        lang: r.lang || 'en',
        reminder_24h_sent: r.reminder_24h_sent === 'TRUE',
        reminder_2h_sent: r.reminder_2h_sent === 'TRUE',
        noshow_recovery_sent: r.noshow_recovery_sent === 'TRUE',
        feedback_sent: r.feedback_sent === 'TRUE',
        feedback_rating: (!isNaN(rating) && rating >= 1 && rating <= 5) ? rating : null,
        google_review_sent: r.google_review_sent === 'TRUE',
        created_at: r.created_at,
      };
    });
}

export async function fetchPatients(apiKey: string, spreadsheetId: string): Promise<Patient[]> {
  const rows = await fetchRange(apiKey, spreadsheetId, 'Sessions!A:K');
  if (rows.length < 2) return [];
  const [headers, ...data] = rows;
  return data
    .filter(row => row.length > 0 && row[0])
    .map(row => rowToObject(headers, row) as unknown as Patient);
}

export function parseConversation(json: string): ConversationMessage[] {
  try {
    if (!json || json === '[]') return [];
    return JSON.parse(json) as ConversationMessage[];
  } catch {
    return [];
  }
}
