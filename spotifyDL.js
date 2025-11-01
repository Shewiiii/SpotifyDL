(async function downloadButton() {
  console.log("caca");

  if (!Spicetify.React || !Spicetify.ReactDOM || !Spicetify.ContextMenu) {
    setTimeout(downloadButton, 300);
    return;
  }

  const downloadItem = new Spicetify.ContextMenu.Item(
    "Download",
    async (uris) => {
      for (const uri of uris) {
        try {
          const elementId = uri.split(":")[2];
          const elementType = uri.split(":")[1];
          const elementUrl = `https://api.spotify.com/v1/${
            elementType === "track" ? "tracks" : elementType + "s"
          }/${elementId}`;
          const elementData = await Spicetify.CosmosAsync.get(elementUrl);
          const elementName = elementData.name;

          let displayName;
          if (elementData.artists) {
            displayName = `${elementData.artists[0].name} - ${elementName}`;
          } else {
            displayName = elementName;
          }

          Spicetify.showNotification(
            `Downloading ${displayName}..`,
            false,
            3000
          );

          fetch(`http://localhost:5000/${elementType}/${elementId}`, {
            method: "GET",
          })
            .then((response) => {
              if (response.ok) {
                Spicetify.showNotification(
                  `Successfully downloaded ${displayName} !`,
                  false,
                  3000
                );
              } else {
                Spicetify.showNotification(
                  `Error ${response.status}`,
                  true,
                  3000
                );
              }
            })
            .catch((error) => {
              console.error(error);
              Spicetify.showNotification(
                `${error}. Make sure the SpotifyDL server is running.`,
                true,
                3000
              );
            });
        } catch (error) {
          console.error("Error during URI parsing:", error);
        }
      }
    },
    // If is track, album, playlist or artist
    (uris) => {
      if (!uris) return false;
      const validTypes = ["track", "album", "playlist", "artist"];
      return validTypes.some((type) => uris[0].includes(`spotify:${type}:`));
    },
    `<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 12l-4-4h2.5V4h3v4H12l-4 4z"/><path d="M14 13v1H2v-1h12z"/></svg>`,
    false
  );

  downloadItem.register();
  console.log("Download button loaded");
})();
