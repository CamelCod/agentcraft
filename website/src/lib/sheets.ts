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

export interface Doctor {
  id: string;
  name_en: string;
  name_ar: string;
  specialty: string;
  active: boolean;
}

export interface ConversationMessage {
  role: 'patient' | 'bot';
  text: string;
  timestamp?: string;
}

const SHEETS_API_BASE = 'https://sheets.googleapis.com/v4/spreadsheets';

function getSheetsConfig() {
  const apiKey = import.meta.env.PUBLIC_SHEETS_API_KEY;
  const spreadsheetId = import.meta.env.PUBLIC_CLINIC_SPREADSHEET_ID;
  return { apiKey, spreadsheetId };
}

async function fetchRange(range: string): Promise<string[][]> {
  const { apiKey, spreadsheetId } = getSheetsConfig();
  if (!apiKey || !spreadsheetId) {
    console.warn('Sheets API key or spreadsheet ID not configured');
    return [];
  }
  const url = `${SHEETS_API_BASE}/${spreadsheetId}/values/${encodeURIComponent(range)}?key=${apiKey}`;
  const res = await fetch(url);
  if (!res.ok) {
    console.error(`Sheets fetch error: ${res.status} ${res.statusText}`);
    return [];
  }
  const data = await res.json();
  return data.values ?? [];
}

function rowToObject(headers: string[], row: string[]): Record<string, string> {
  const obj: Record<string, string> = {};
  headers.forEach((h, i) => { obj[h] = row[i] ?? ''; });
  return obj;
}

export async function fetchAppointments(): Promise<Appointment[]> {
  const rows = await fetchRange('Appointments!A:O');
  if (rows.length < 2) return [];
  const [headers, ...data] = rows;
  return data
    .filter(row => row.length > 0 && row[0])
    .map(row => {
      const r = rowToObject(headers, row);
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
        feedback_rating: (() => { const v = parseInt(r.feedback_rating, 10); return (!isNaN(v) && v >= 1 && v <= 5) ? v : null; })(),
        google_review_sent: r.google_review_sent === 'TRUE',
        created_at: r.created_at,
      };
    });
}

export async function fetchPatients(): Promise<Patient[]> {
  const rows = await fetchRange('Sessions!A:K');
  if (rows.length < 2) return [];
  const [headers, ...data] = rows;
  return data
    .filter(row => row.length > 0 && row[0])
    .map(row => rowToObject(headers, row) as unknown as Patient);
}

export async function fetchDoctors(): Promise<Doctor[]> {
  const rows = await fetchRange('Doctors!A:E');
  if (rows.length < 2) return [];
  const [headers, ...data] = rows;
  return data
    .filter(row => row.length > 0 && row[0])
    .map(row => {
      const r = rowToObject(headers, row);
      return {
        id: r.id,
        name_en: r.name_en,
        name_ar: r.name_ar,
        specialty: r.specialty,
        active: r.active === 'TRUE',
      };
    });
}

export function parseConversation(json: string): ConversationMessage[] {
  try {
    if (!json || json === '[]') return [];
    return JSON.parse(json) as ConversationMessage[];
  } catch {
    return [];
  }
}

export const LANG_FLAGS: Record<string, string> = {
  ar: '🇦🇪',
  en: '🇬🇧',
  hi: '🇮🇳',
  ur: '🇵🇰',
  tl: '🇵🇭',
  ml: '🇮🇳',
  fr: '🇫🇷',
};

export const LANG_NAMES: Record<string, string> = {
  ar: 'Arabic',
  en: 'English',
  hi: 'Hindi',
  ur: 'Urdu',
  tl: 'Filipino',
  ml: 'Malayalam',
  fr: 'French',
};
