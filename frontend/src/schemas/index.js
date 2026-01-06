import * as yup from "yup";

const uzbPhoneRegExp = /^998[0-9]{9}$/;

export const loginSchema = yup.object().shape({
  phone: yup
    .string()
    // .matches(uzbPhoneRegExp, "Telefon raqam faqat 998XXXXXXXXX formatda bo'lishi kerak")
    .required("Telefon raqam kiritish majburiy!"),
  password: yup.string().required("parol kiritish majburiy"),
});


export const newsSchema = yup.object().shape({
  title: yup.string().required().min(3).max(50),
  text: yup.string().required().min(15).max(2000),
})