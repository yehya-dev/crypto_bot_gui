let form = document.getElementById("get-symbol");
let base = form.querySelector("#base");
let quote = form.querySelector("#quote");
let buy_perc = form.querySelector("#buy-perc");

form.addEventListener("submit", (event) => {
  event.preventDefault();
  fetch(
    "/addcoin?" +
      new URLSearchParams({
        base: base.value.toUpperCase(),
        quote: quote.value.toUpperCase(),
        percent: buy_perc.value,
      })
  );
});

let coin_list_refresh = document.getElementById("coin-list_refresh");
let coin_list = document.getElementById("coin-list");

coin_list.addEventListener("submit", (event) => {
  event.preventDefault();
  let formelm = event.target;
  fetch("/buycoin", {
    method: "POST",
    body: new FormData(formelm),
  });
});

coin_list_refresh.addEventListener("click", (event) => {
  fetch("/getcoins")
    .then((response) => {
      return response.json();
    })
    .then((response) => {
      coin_list.innerHTML = "";
      for (const coin in response) {
        let listitem = document.createElement("li");
        listitem.className = "list-item p-3 flex flex-col";
        let heading = document.createElement("p");
        heading.className = "font-bold text-xl"
        heading.innerHTML = coin + " - " + response[coin];
        let base, quote;
        [base, quote] = coin.split(" ");
        let buy_form = document.createElement("form");
        buy_form.className = "flex flex-col gap-3"
        let stop_tsl = document.createElement("button");
        stop_tsl.innerHTML = "STOP TSL";
        stop_tsl.className =
          "p-1 font-bold bg-blue-600 text-gray-100 rounded-md";
        stop_tsl.addEventListener("click", (event) => {
          fetch(
            "/stoptsl?" +
              new URLSearchParams({
                base: base,
                quote: quote,
              })
          );
        });

        let sell_all = document.createElement("button");
        sell_all.className = 'p-1 font-bold bg-blue-600 text-gray-100 rounded-md';
        sell_all.addEventListener("click", (event) => {
          fetch(
            "/sellall?" +
              new URLSearchParams({
                base: base,
                quote: quote,
              })
          );
        });

        sell_all.innerHTML = "SELL ALL";

        let base_input = document.createElement("input");
        base_input.name = "base";
        base_input.value = base;
        let quote_input = document.createElement("input");
        quote_input.name = "quote";
        quote_input.value = quote;
        base_input.type = quote_input.type = "hidden";

        let buyelem = `<div class="flex flex-col">
            <label for="buy_percentage">Percentage (BUY)</label>
            <input class="font-bold p-1 text-green-500" id="buy_percentage" name="buy_percentage" type="text" value="10"/>
            <div>
            `;
        let tsl = `<div class="flex flex-col">
            <label for="follow_percentage">TSL Follow percent</label>
            <input class="font-bold p-1 text-green-500" id="follow_percentage" name="follow_percentage" type="text" value="10"/>
            </div>
            <div class="flex flex-col">
            <label for="safety_percentage">TSL Safety percent</label>
            <input class="font-bold p-1 text-green-500" id="safety_percentage" name="safety_percentage" type="text" value="1"/>
            </div>
            `;
        let button = document.createElement("button");
        button.type = "submit";
        button.className = "p-1 font-bold bg-blue-600 text-gray-100 rounded-md";
        button.innerText = "Buy/TSL";
        let close_button = document.createElement("button");
        close_button.innerHTML = "REMOVE";
        close_button.className = 'p-1 font-bold bg-blue-600 text-gray-100 rounded-md';
        close_button.addEventListener("click", (event) => {
          fetch(
            "/removecoin?" +
              new URLSearchParams({
                base: base,
                quote: quote,
              })
          );
        });
        let contain1 = document.createElement("section");
        let contain2 = document.createElement("section");
        contain1.className = "flex flex-col gap-3"
        contain2.className = "flex flex-col gap-3"
        contain2.innerHTML = `
        <form class="flex flex-col gap-2 my-2" id="multi-limit">
          <input type="hidden" name="base" value="${base}"/>
          <input type="hidden" name="quote" value="${quote}"/>
          <div class="flex flex-col">
          <label for="sell-percent">Sell Percentages</label>
          <input class="p-1 font-bold text-green-500" id="sell-percent" type="text" name="sell-perc"/>
          </div>
          <div class="flex flex-col">
          <label for="sell-quantity">Sell Quantities</label>
          <input class="p-1 font-bold text-green-500" id="sell-quantitiy" type="text" name="sell-quant"/>
          </div>
          <button class="p-1 font-bold bg-blue-600 text-gray-100 rounded-md" type="submit">Set Limits</button>
          </form>
        `;
        let multi_form = contain2.querySelector("#multi-limit");
        multi_form.addEventListener("submit", (event) => {
          event.preventDefault();
          event.stopPropagation();
          fetch("/multilimit", {
            method: "POST",
            body: new FormData(multi_form),
          });
        });

        buy_form.appendChild(heading);
        buy_form.appendChild(base_input);
        buy_form.appendChild(quote_input);
        buy_form.insertAdjacentHTML("beforeend", buyelem);
        buy_form.insertAdjacentHTML("beforeend", tsl);
        buy_form.appendChild(button);
        contain1.appendChild(buy_form);
        contain1.appendChild(stop_tsl);
        contain1.appendChild(sell_all);
        contain1.appendChild(close_button);
        listitem.appendChild(contain1);
        listitem.appendChild(contain2);
        coin_list.appendChild(listitem);
      }
    })
    .catch((error) => {
      console.log(error);
    });
});
