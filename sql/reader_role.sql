-- Run once in Supabase SQL Editor. Replace the placeholder with a NEW strong password.
-- Never commit a file containing the real password.
CREATE ROLE quiz_reader LOGIN PASSWORD 'REPLACE_WITH_NEW_STRONG_PASSWORD';
GRANT USAGE ON SCHEMA public TO quiz_reader;
GRANT SELECT ON public.customers, public.products, public.orders,
    public.quiz_questions TO quiz_reader;
CREATE POLICY "Reader customers" ON public.customers
    FOR SELECT TO quiz_reader USING (true);
CREATE POLICY "Reader products" ON public.products
    FOR SELECT TO quiz_reader USING (true);
CREATE POLICY "Reader orders" ON public.orders
    FOR SELECT TO quiz_reader USING (true);
CREATE POLICY "Reader questions" ON public.quiz_questions
    FOR SELECT TO quiz_reader USING (true);
