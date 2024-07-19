import mongoose from "mongoose";
import fs from "fs";
import cloudinary from "cloudinary";
import dotenv from "dotenv";

dotenv.config();
mongoose.connect(process.env.MONGO_URI);

mongoose.set("strictQuery", true);
const db = mongoose.connection;
cloudinary.v2.config({
  cloud_name: process.env.CLOUDINARY_CLIENT_NAME,
  api_key: process.env.CLOUDINARY_CLIENT_API,
  api_secret: process.env.CLOUDINARY_CLIENT_SECRET,
});

db.on("error", console.error.bind(console, "MongoDB connection error:"));
db.once("open", () => {
  console.log("Connected to MongoDB");
  uploadData();
});

const uploadToCloudinary = async (fileUri, folder) => {
  try {
    const data = await cloudinary.v2.uploader.upload(fileUri, { folder });
    return { url: data.url, public_id: data.public_id };
  } catch (error) {
    console.error(error);
    throw error;
  }
};

async function uploadData() {
  try {
    const data = JSON.parse(fs.readFileSync("linkedin_posts.json", "utf8"));
    console.log(data);

    // Upload images to Cloudinary and update data with Cloudinary URLs
    for (let item of data) {
      if (item.image) {
        const result = await uploadToCloudinary(item.image, "post-images");
        console.log(result);
        if (result) {
          item.image = {
            public_id: result.public_id,
            url: result.url,
          };
        }
      }
    }

    const Schema = new mongoose.Schema({}, { strict: false });
    const Post = mongoose.model("Post", Schema, "posts");
    console.log("starting inserting data");
    const result = await Post.insertMany(data);
    console.log(`${result.length} documents were inserted`);
  } catch (error) {
    console.error("Error uploading data:", error);
  } finally {
    db.close();
  }
}
