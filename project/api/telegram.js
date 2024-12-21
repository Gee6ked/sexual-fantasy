// api/telegram.js
export default async function handler(req, res) {
    if (req.method === 'POST') {
        const { type, data } = req.body;

        // Ваша логика обработки данных
        console.log(`Received ${type} data:`, data);

        // Пример ответа
        res.status(200).json({ success: true });
    } else {
        res.status(405).json({ error: 'Method Not Allowed' });
    }
}